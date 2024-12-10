atc \
  --model=./burpee_detection.onnx \
  --framework=5 \
  --output=./burpee_detection \
  --input_format=NCHW \
  --input_shape="images:1,3,640,640"  \
  --out_nodes="Transpose_213:0;Transpose_262:0;Transpose_311:0"  \
  --enable_small_channel=1 \
  --insert_op_conf=./aipp_yolov5.cfg \
  --soc_version=Ascend310P3 \
  --log=info
  
