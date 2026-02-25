"""
Copyright 2026 Huawei Technologies Co., Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import time
import random
import asyncio
import multiprocessing
import argparse
import socket
import uvicorn
import aiohttp
from typing import List
from itertools import islice
from tqdm import tqdm
from fastapi import FastAPI, HTTPException
from aiohttp import web

from examples.agents.websearcher.retrieval_server.utils.config import RetrieverConfig, QueryRequest
from examples.agents.websearcher.retrieval_server.utils.output_manager import OutputLogger, OutputQueueHandler
from examples.agents.websearcher.retrieval_server.utils.retriever import DenseRetriever


config: RetrieverConfig = None
retriever: DenseRetriever = None

def start_backend_server(args, port: int, status_queue: multiprocessing.Queue, output_queue: multiprocessing.Queue, idx=0):
    """Starts a backend server instance with given configuration.

       This function initializes a retrieval server, reports its status, and runs 
       an ASGI server on the specified port.

       Args:
            args: Command-line arguments containing configuration parameters.
            port: The port number for the server to listen on.
            status_queue: Queue for sending initialization status to the main process.
            output_queue: Queue for capturing subprocess output (handled by context manager).
            idx: Instance index for logging identification (default: 0).
    """
    idx += 1
    global config, retriever
    pid = os.getpid()
    with OutputQueueHandler(output_queue, port, pid):
        # 1) Build a config (could also parse from arguments).
        #    In real usage, you'd parse your CLI arguments or environment variables.
        config = RetrieverConfig(
            retrieval_method=args.retriever_name,  # or "dense"
            index_path=args.index_path,
            corpus_path=args.corpus_path,
            retrieval_topk=args.topk,
            faiss_gpu=args.faiss_gpu,
            retrieval_model_path=args.retriever_model,
            retrieval_pooling_method="mean",
            retrieval_query_max_length=256,
            retrieval_use_fp16=True,
            retrieval_batch_size=512,
        )

        # 2) Instantiate a global retriever so it is loaded once and reused.
        retriever = DenseRetriever(config, port)
        print(f"idx: {idx}; PORT{port}: Retriver is ready.")

        # 3) Launch the server.
        status_queue.put((port, "success"))
        print(f"idx: {idx}; PORT{port}: Server init finish!")
        uvicorn.run(app, host="127.0.0.1", port=port)


def get_available_ports(count: int, args, start_range: int = 20000, end_range: int = 30000):
    """Finds a specified number of available TCP ports within a given range.

        Args:
            count: Number of required available ports. Must be at least 1.
            args: Object containing the main service port to exclude (must have 'port' attribute).
            start_range: Start of the port range to search (inclusive). Defaults to 20000.
            end_range: End of the port range to search (inclusive). Defaults to 30000.

        Returns:
            A list of available ports. The list length will be equal to the requested count.
        """
    if end_range <= start_range:
        raise ValueError("Invalid port range")
    if count < 1:
        raise ValueError("count must be at least 1")

    def is_port_available(port: int) -> bool:
        """Checks if a TCP port is available for use on localhost."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", port))
            return True
        except Exception:
            return False  
    
    ports = [p for p in range(start_range, end_range + 1) if p != args.port]
    random.shuffle(ports)

    available_port_generator = (
        port for port in ports 
        if is_port_available(port)
    )

    available_ports = list(islice(available_port_generator, count))

    if len(available_ports) < count:
        raise RuntimeError(f"Insufficient available ports (found {len(available_ports)})")

    return available_ports

class LoadBalancer:
    """HTTP load balancer with health checking and round-robin routing."""
    def __init__(self, backend_ports: List[int], proxy_port: int = 8000):
        """Initialize the load balancer.
        
        Args:
            backend_ports: List of backend service ports
            proxy_port: Port to listen for incoming requests (default: 8000)
        """
        self.backend_ports = backend_ports
        self.proxy_port = proxy_port
        self.backends = [f"http://127.0.0.1:{port}" for port in backend_ports]
        self.healthy_backends = self.backends.copy()
        self.current_index = 0
        self.health_check_interval = 60

    def run(self):
        """Start the load balancer service.
        
        Sets up web server and health check coroutine.
        """
        application = web.Application()
        application.router.add_route('*', '/{path:.*}', self.proxy_request)

        loop = asyncio.get_event_loop()
        loop.create_task(self.health_check())

        web.run_app(application, host="127.0.0.1", port=self.proxy_port)

    async def health_check(self):
        """Periodically check backend health status.
        
        Runs in background coroutine, updates healthy_backends list.
        """
        while True:
            async with aiohttp.ClientSession() as session:
                new_healthy = await self._check_all_backends(session)
            self.healthy_backends = new_healthy
            await asyncio.sleep(self.health_check_interval)

    def get_next_backend(self) -> str:        
        """Select next available backend using round-robin algorithm.
        
        Returns:
            URL of the selected backend
            
        Raises:
            HTTPException: If no healthy backends available
        """        
        if not self.healthy_backends:
            raise HTTPException(status_code=503, detail="No healthy backends available")
        backend = self.healthy_backends[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.healthy_backends)
        return backend

    async def proxy_request(self, request: web.Request) -> web.Response:
        """Proxy incoming request to a backend service.
        
        Args:
            request: Incoming HTTP request
            
        Returns:
            Response from backend service
        """
        try:
            backend = self.get_next_backend()
            path = request.path_qs
            url = f"{backend}{path}"

            async with aiohttp.ClientSession() as session:
                async with session.request(
                        method=request.method,
                        url=url,
                        headers=request.headers,
                        data=await request.read(),
                        timeout=6000
                ) as resp:
                    return web.Response(
                        body=await resp.read(),
                        status=resp.status,
                        headers=resp.headers
                    )
        except Exception as e:
            return web.Response(text=str(e), status=500)

    async def _check_all_backends(self, session):
        """Check health status of all backends.
        
        Args:
            session: Aiohttp session for making requests
            
        Returns:
            List of healthy backend URLs
        """
        healthy = []
        for backend in self.backends:
            if await self._is_backend_healthy(session, backend):
                healthy.append(backend)
        return healthy

    async def _is_backend_healthy(self, session, backend):
        """Check if a single backend is healthy.
        
        Args:
            session: Aiohttp session
            backend: Backend URL to check
            
        Returns:
            bool: True if backend is healthy
        """
        try:
            async with session.get(f"{backend}/health", timeout=6000) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False


app = FastAPI()

@app.post("/retrieve")
async def retrieve_endpoint(request: QueryRequest):
    """Endpoint that accepts queries and performs retrieval.
    
    Args:
        request: QueryRequest object containing:
            - queries: List of query strings for retrieval
            - topk: Number of results to return per query (optional, defaults to config)
            - return_scores: Whether to include similarity scores in results

    Note:
        Input format:
            {
            "queries": ["What is Python?", "Tell me about neural networks."],
            "topk": 3,
            "return_scores": true
            }
    """
    if not isinstance(request.topk, int) or request.topk <= 0:
        request.topk = config.retrieval_topk
    print(f"retrieve input: {request}")
    # Perform batch retrieval
    try:
        results, scores = retriever.batch_search(
            query_list=request.queries,
            num=request.topk
        )
    except Exception as e:
        raise HTTPException(status_code=500) from e
        
    # Format response
    resp = []
    for i, single_result in enumerate(results):
        if request.return_scores:
            # If scores are returned, combine them with results
            combined = []
            for doc, score in zip(single_result, scores[i]):
                combined.append({"document": doc, "score": score})
            resp.append(combined)
        else:
            resp.append(single_result)
    print(f"retrieve output: {resp}")
    return {"result": resp}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch the local faiss retriever.")
    parser.add_argument("--index_path", type=str, required=True, help="Path of the corpus indexing file.")
    parser.add_argument("--corpus_path", type=str, required=True, help="Path of the ocal corpus file.")
    parser.add_argument("--topk", type=int, default=5, help="Number of retrieved passages for one query.")
    parser.add_argument("--retriever_name", type=str, default="e5", help="Name of the retriever model.")
    parser.add_argument("--retriever_model", type=str, required=True, help="Path of the retriever model.")
    parser.add_argument('--faiss_gpu', action='store_true', help='Use GPU for computation')
    parser.add_argument("--port", type=int, default=5005)
    parser.add_argument('--backend_count', type=int, default=3, help="Number of backend proxy load balancing threads")

    args = parser.parse_args()
    
    print(f"Server address: {'127.0.0.1':{args.port}}")

    backend_ports = get_available_ports(count=args.backend_count, args=args)

    manager = multiprocessing.Manager()
    status_queue = manager.Queue()      # Used to pass initialization status of subprocess
    output_queue = manager.Queue()      # Used to pass subprocess output

    # Start output logger thread (main process thread)
    output_logger = OutputLogger(output_queue)
    output_logger.start()

    backend_processes = []
    for idx, port in enumerate(backend_ports):
        process = multiprocessing.Process(
            target=start_backend_server,
            args=(args, port, status_queue, output_queue, idx),
            daemon=True,
        )
        process.start()
        backend_processes.append(process)
        print(f"Starting backend service: 127.0.0.1:{port}")
        time.sleep(100)

    progress_bar = tqdm(total=len(backend_ports), desc="Initialization progress")
    completed_count = 0

    # Listen to status queue to update progress
    while completed_count < len(backend_ports):
        try:
            # Timeout waiting to avoid infinite blocking
            port, status = status_queue.get(timeout=6000)
            completed_count += 1
            progress_bar.update(1)
        except Exception as e:
            # Handle timeout or queue errors
            progress_bar.set_postfix({"Warning": "Partial process response timeout"})
            break

    progress_bar.close()

    print(f"Starting load balancer: 127.0.0.1:{args.port}")
    load_balancer = LoadBalancer(
        backend_ports=backend_ports,
        proxy_port=args.port
    )
    try:
        load_balancer.run()
    finally:
        for p in backend_processes:
            p.terminate()

        output_queue.put(None)  # Send termination signal
        output_logger.join(timeout=2)
        manager.shutdown()