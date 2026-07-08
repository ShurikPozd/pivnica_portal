import pandas as pd
import numpy as np
import pickle
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix


class DishRecommender:
    """
    Рекомендательная система для блюд ресторана.
    """
    
    def __init__(self):
        self.dishes_df = None
        self.dish_features_matrix = None
        self.dish_ids = None
        self.tfidf = None
        self.is_trained = False
    
    def train(self, dishes_df, categories_df):
        """
        Обучает модель на основе данных о блюдах и категориях.
        """
        print("🚀 Начинаем обучение модели...")
        
        # Сохраняем данные
        self.dishes_df = dishes_df.copy()
        
        # Объединяем с категориями
        dishes_with_cat = dishes_df.merge(categories_df, left_on='category_id', right_on='id', suffixes=('', '_cat'))
        
        # Создаём текстовые признаки для TF-IDF
        dishes_with_cat['features'] = (
            dishes_with_cat['name'].fillna('') + ' ' +
            dishes_with_cat['name_cat'].fillna('') + ' ' +
            dishes_with_cat['description'].fillna('')
        )
        
        # TF-IDF векторизация
        self.tfidf = TfidfVectorizer(
            stop_words='english',
            max_features=100
        )
        
        # Обучаем TF-IDF
        self.dish_features_matrix = self.tfidf.fit_transform(dishes_with_cat['features'])
        self.dish_ids = dishes_with_cat['id'].values
        
        self.is_trained = True
        print(f"✅ Модель обучена! {len(self.dish_ids)} блюд")
        return self
    
    def recommend(self, dish_id, n=5):
        """
        Рекомендует n блюд, похожих на dish_id.
        """
        if not self.is_trained:
            raise ValueError("Модель не обучена. Вызовите train() сначала.")
        
        # Находим индекс блюда
        try:
            idx = np.where(self.dish_ids == dish_id)[0][0]
        except IndexError:
            print(f"⚠️ Блюдо с id={dish_id} не найдено")
            return []
        
        # Вычисляем косинусное сходство
        dish_vector = self.dish_features_matrix[idx]
        similarities = cosine_similarity(dish_vector, self.dish_features_matrix).flatten()
        
        # Получаем топ-n похожих блюд (исключая само блюдо)
        similar_indices = similarities.argsort()[::-1][1:n+1]
        recommended_ids = self.dish_ids[similar_indices]
        recommended_scores = similarities[similar_indices]
        
        # Формируем результат
        result = []
        for rec_id, score in zip(recommended_ids, recommended_scores):
            dish_data = self.dishes_df[self.dishes_df['id'] == rec_id].iloc[0]
            result.append({
                'id': int(rec_id),
                'name': dish_data['name'],
                'price': float(dish_data['price']),
                'similarity': float(score)
            })
        
        return result
    
    def recommend_popular(self, reservations_df, n=5):
        """
        Рекомендует самые популярные блюда на основе истории бронирований.
        """
        # TODO: Связать бронирования с блюдами через меню
        # Пока возвращаем случайные блюда
        sample = self.dishes_df.sample(min(n, len(self.dishes_df)))
        return sample[['id', 'name', 'price']].to_dict('records')
    
    def save(self, path='ml/models/recommender.pkl'):
        """Сохраняет модель в файл."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        print(f"✅ Модель сохранена в {path}")
    
    @classmethod
    def load(cls, path='ml/models/recommender.pkl'):
        """Загружает модель из файла."""
        with open(path, 'rb') as f:
            return pickle.load(f)


def create_simple_recommendations(dishes_df, categories_df):
    """
    Создаёт простые рекомендации: топ-5 блюд в каждой категории.
    """
    # Объединяем с категориями
    dishes_with_cat = dishes_df.merge(categories_df, left_on='category_id', right_on='id', suffixes=('', '_cat'))
    
    # Группируем по категориям
    recommendations = {}
    for category in dishes_with_cat['name_cat'].unique():
        top_dishes = dishes_with_cat[dishes_with_cat['name_cat'] == category].nlargest(5, 'price')
        recommendations[category] = top_dishes[['id', 'name', 'price']].to_dict('records')
    
    return recommendations