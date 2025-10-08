from ultralytics import YOLO
import yaml

# Загрузка модели
model = YOLO('yolov8n.pt')

results = model.train(
    data='datasets/data.yaml',
    epochs=30,
    patience=10,  # ранняя остановка
    batch=16,
    imgsz=640,
    save=True,
    save_period=10,  # сохранять чекпоинты каждые 10 эпох # использовать GPU
    workers=4,
    optimizer='AdamW',
    lr0=0.001,
    warmup_epochs=3
)

# Валидация после обучения
metrics = model.val()
print("mAP50:", metrics.box.map50)
print("mAP50-95:", metrics.box.map)
print("Precision:", metrics.box.mp)
print("Recall:", metrics.box.mr)

# Детальный анализ
if hasattr(metrics, 'results_dict'):
    for key, value in metrics.results_dict.items():
        print(f"{key}: {value}")
# Предсказание на новых изображения
results = model.predict('test_photo_jpg.rf.c63b8c2ca999640bf91069ce3487978d.jpg', save=True)
