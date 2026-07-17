import os  
import torch  
from ultralytics import YOLO  
import torchvision.transforms as transforms
from PIL import Image  
from torchvision.models import efficientnet_b4


img_transforms = transforms.Compose([
    transforms.Resize((380, 380)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


def load_efficientnet_model(model_path, num_classes):
    model = efficientnet_b4()
    num_features = model.classifier[1].in_features
    model.classifier[1] = torch.nn.Linear(num_features, num_classes)
    
    
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()  
    return model


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(CURRENT_DIR, "models")

YOLO_MODEL_PATH = os.path.join(MODELS_DIR, "salkım_best.pt")
RIPENESS_MODEL_PATH = os.path.join(MODELS_DIR, "salkım_ripeness.pth")
DISEASE_MODEL_PATH = os.path.join(MODELS_DIR, "salkım_efficientnet.pth")


print("--- Model Dosyaları Kontrol Ediliyor ---")
print("YOLO Modeli Var mı?:", os.path.exists(YOLO_MODEL_PATH))
print("Olgunluk Modeli Var mı?:", os.path.exists(RIPENESS_MODEL_PATH))
print("Hastalık Modeli Var mı?:", os.path.exists(DISEASE_MODEL_PATH))


def full_analysis(image_path):
    print(f"\n[INFO] {image_path} için uçtan uca analiz başlatıldı...")
    
    
    yolo_model = YOLO(YOLO_MODEL_PATH)
    ripeness_model = load_efficientnet_model(RIPENESS_MODEL_PATH, num_classes=3)
    disease_model = load_efficientnet_model(DISEASE_MODEL_PATH, num_classes=5)
    
    
    img = Image.open(image_path).convert('RGB')
    results = yolo_model(image_path)
    detected_boxes = results[0].boxes
    
    print(f"[YOLO] Fotoğrafta toplam {len(detected_boxes)} adet domates tespit edildi.")
    
    tomatoes_analysis = []
    
    
    for i, box in enumerate(detected_boxes):
        xyxy = box.xyxy[0].tolist()
        cropped_img = img.crop((xyxy[0], xyxy[1], xyxy[2], xyxy[3]))
        input_tensor = img_transforms(cropped_img).unsqueeze(0)
        
        with torch.no_grad():
            ripeness_output = ripeness_model(input_tensor)
            disease_output = disease_model(input_tensor)
            
            ripeness_cls = torch.argmax(ripeness_output, dim=1).item()
            disease_cls = torch.argmax(disease_output, dim=1).item()
        
        tomatoes_analysis.append({
            "tomato_id": i + 1,
            "ripeness_class_id": ripeness_cls,
            "disease_class_id": disease_cls
        })
        print(f" -> Domates #{i+1}: Olgunluk ID: {ripeness_cls} | Hastalık ID: {disease_cls}")
        
    return {
        "total_tomatoes": len(detected_boxes),
        "results": tomatoes_analysis
    }


if __name__ == "__main__":
    print("\n--- Sistem ve fonksiyonlar sorunsuz yüklendi! ---")