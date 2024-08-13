import cv2
import os

folder_path = './data/FIRE/Images/'
output_folder = os.path.join(folder_path, 'resized')
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    if os.path.isfile(file_path) and filename.lower().endswith(('.jpg')):
        img = cv2.imread(file_path)
        if img is not None:
            resized_img = cv2.resize(img, (768, 768))
            output_path = os.path.join(output_folder, filename)
            cv2.imwrite(output_path, resized_img)
print("Resized images path:", output_folder)

scale_factor = 768 / 2912
ground_truth_folder = r'./data/FIRE/Ground Truth'
output_folder = os.path.join(ground_truth_folder, 'resized')
os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(ground_truth_folder):
    if filename.lower().endswith('.txt'):
        ground_truth_file = os.path.join(ground_truth_folder, filename)
        output_file = os.path.join(output_folder, filename)
        with open(ground_truth_file, 'r') as f:
            lines = f.readlines()
        with open(output_file, 'w') as f:
            for line in lines:
                coords = line.strip().split()
                scaled_coords = [str(float(coord) * scale_factor) for coord in coords]
                f.write(' '.join(scaled_coords) + '\n')
print("Resized ground truth path:", output_folder)