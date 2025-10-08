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

