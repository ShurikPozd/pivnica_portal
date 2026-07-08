import os
import django
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pivnica.settings')
django.setup()

from ml.data_loader import load_data_to_csv
from ml.recommender import DishRecommender
from portal.models import Dish, Category

def train_and_save():
    """Обучает модель и сохраняет её."""
    
    # 1. Загружаем данные
    print("📊 Загрузка данных...")
    data = load_data_to_csv()
    
    # 2. Получаем данные из БД
    dishes_df = pd.DataFrame(list(Dish.objects.all().values()))
    categories_df = pd.DataFrame(list(Category.objects.all().values()))
    
    # 3. Обучаем модель
    print("🤖 Обучение модели...")
    recommender = DishRecommender()
    recommender.train(dishes_df, categories_df)
    
    # 4. Сохраняем
    recommender.save('ml/models/recommender.pkl')
    
    # 5. Тестируем
    print("\n🧪 Тестирование модели:")
    if len(dishes_df) > 0:
        test_dish = dishes_df.iloc[0]
        recs = recommender.recommend(test_dish['id'], n=3)
        print(f"  Для блюда '{test_dish['name']}' рекомендуем:")
        for rec in recs:
            print(f"    - {rec['name']} (похожесть: {rec['similarity']:.2f})")
    
    print("\n✅ Готово!")

if __name__ == '__main__':
    train_and_save()