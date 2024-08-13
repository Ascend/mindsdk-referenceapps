import cv2
import os

folder_path = './data/FIRE/Images'
output_folder = os.path.join(folder_path,'resized')
os.makedirs(output_folder, exist_ok = True)

for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    if os.path.isfile(file_path) and filename.lower().endswith('.jpg'):
        img = cv2.imread(file_path)
        if img is not None:
            resized_img = cv2.resize(img,(768,768))
            output_path = os.path.join(output_folder,filename)
            cv2.imwrite(output_path,resized_img)