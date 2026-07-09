import pandas as pd
import numpy as np
import pickle
import os
import datetime
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.db.models import Count, Sum, Avg

from portal.models import Dish, OrderItem, Order, Category, SiteSettings


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
        print("🚀 Начинаем обучение модели...")
        
        self.dishes_df = dishes_df.copy()
        
        dishes_with_cat = dishes_df.merge(categories_df, left_on='category_id', right_on='id', suffixes=('', '_cat'))
        
        dishes_with_cat['features'] = (
            dishes_with_cat['name'].fillna('') + ' ' +
            dishes_with_cat['name_cat'].fillna('') + ' ' +
            dishes_with_cat.get('description', '').fillna('')
        )
        
        self.tfidf = TfidfVectorizer(
            stop_words='english',
            max_features=100
        )
        
        self.dish_features_matrix = self.tfidf.fit_transform(dishes_with_cat['features'])
        self.dish_ids = dishes_with_cat['id'].values
        
        self.is_trained = True
        print(f"✅ Модель обучена! {len(self.dish_ids)} блюд")
        return self
    
    def _get_recommendations_count(self, default=5):
        """Получает количество рекомендаций из настроек сайта."""
        try:
            settings = SiteSettings.objects.first()
            if settings:
                return settings.recommendations_count
        except:
            pass
        return default
    
    def recommend(self, dish_id, n=None):
        if n is None:
            n = self._get_recommendations_count()
        
        if not self.is_trained:
            raise ValueError("Модель не обучена. Вызовите train() сначала.")
        
        try:
            idx = np.where(self.dish_ids == dish_id)[0][0]
        except IndexError:
            print(f"⚠️ Блюдо с id={dish_id} не найдено")
            return []
        
        dish_vector = self.dish_features_matrix[idx]
        similarities = cosine_similarity(dish_vector, self.dish_features_matrix).flatten()
        
        similar_indices = similarities.argsort()[::-1][1:n+1]
        recommended_ids = self.dish_ids[similar_indices]
        recommended_scores = similarities[similar_indices]
        
        result = []
        for rec_id, score in zip(recommended_ids, recommended_scores):
            dish_data = self.dishes_df[self.dishes_df['id'] == rec_id].iloc[0]
            result.append({
                'id': int(rec_id),
                'name': dish_data['name'],
                'price': float(dish_data['price']),
                'similarity': float(score),
                'category_id': int(dish_data['category_id']) if 'category_id' in dish_data else None
            })
        
        return result
    
    def recommend_random(self, n=None):
        if n is None:
            n = self._get_recommendations_count()
        
        if self.dishes_df is None or len(self.dishes_df) == 0:
            return []
        
        sample = self.dishes_df.sample(min(n, len(self.dishes_df)))
        result = []
        for _, row in sample.iterrows():
            result.append({
                'id': int(row['id']),
                'name': row['name'],
                'price': float(row['price']),
                'category_id': int(row['category_id']) if 'category_id' in row else None
            })
        return result
    
    def recommend_popular(self, n=None):
        if n is None:
            n = self._get_recommendations_count()
        
        try:
            popular_dishes = OrderItem.objects.values('dish_id').annotate(
                total_orders=Count('id')
            ).order_by('-total_orders')[:n]
            
            dish_ids = [item['dish_id'] for item in popular_dishes]
            
            if not dish_ids:
                return self.recommend_random(n)
            
            dishes = Dish.objects.filter(id__in=dish_ids, is_available=True)
            result = []
            for dish in dishes:
                result.append({
                    'id': dish.id,
                    'name': dish.name,
                    'price': float(dish.price),
                    'orders_count': next((item['total_orders'] for item in popular_dishes if item['dish_id'] == dish.id), 0)
                })
            return result
            
        except Exception as e:
            print(f"⚠️ Ошибка в recommend_popular: {e}")
            return self.recommend_random(n)
    
    def recommend_for_customer(self, customer_id, n=None):
        if n is None:
            n = self._get_recommendations_count()
        
        try:
            orders = Order.objects.filter(customer_id=customer_id)
            
            if not orders.exists():
                return self.recommend_popular(n)
            
            ordered_dish_ids = OrderItem.objects.filter(
                order__customer_id=customer_id
            ).values_list('dish_id', flat=True).distinct()
            
            if not ordered_dish_ids:
                return self.recommend_popular(n)
            
            customer_categories = Dish.objects.filter(
                id__in=ordered_dish_ids
            ).values_list('category_id', flat=True).distinct()
            
            recommendations = Dish.objects.filter(
                category_id__in=customer_categories,
                is_available=True
            ).exclude(id__in=ordered_dish_ids)[:n]
            
            if not recommendations:
                return self.recommend_popular(n)
            
            result = []
            for dish in recommendations:
                result.append({
                    'id': dish.id,
                    'name': dish.name,
                    'price': float(dish.price),
                    'category_id': dish.category_id
                })
            return result
            
        except Exception as e:
            print(f"⚠️ Ошибка в recommend_for_customer: {e}")
            return self.recommend_popular(n)
    
    def recommend_by_season(self, n=None):
        if n is None:
            n = self._get_recommendations_count()
        
        month = datetime.datetime.now().month
        
        seasonal_categories = {
            12: ['Новогодние блюда', 'Горячее', 'Праздничные'],
            1: ['Горячее', 'Сытные блюда', 'Супы'],
            2: ['Горячее', 'Сытные блюда', 'Супы'],
            3: ['Супы', 'Горячее', 'Салаты'],
            4: ['Салаты', 'Закуски', 'Горячее'],
            5: ['Салаты', 'Закуски', 'Горячее'],
            6: ['Холодные закуски', 'Салаты', 'Освежающие напитки'],
            7: ['Холодные закуски', 'Салаты', 'Мороженое'],
            8: ['Холодные закуски', 'Салаты', 'Освежающие напитки'],
            9: ['Супы', 'Горячее', 'Салаты'],
            10: ['Супы', 'Горячее', 'Закуски'],
            11: ['Супы', 'Горячее', 'Закуски'],
        }
        
        season_names = {
            6: 'Летние', 7: 'Летние', 8: 'Летние',
            9: 'Осенние', 10: 'Осенние', 11: 'Осенние',
            12: 'Зимние', 1: 'Зимние', 2: 'Зимние',
            3: 'Весенние', 4: 'Весенние', 5: 'Весенние'
        }
        
        category_names = seasonal_categories.get(month, ['Популярные'])
        matching_categories = Category.objects.filter(name__in=category_names)
        cat_ids = [c.id for c in matching_categories]
        
        if cat_ids:
            dishes = Dish.objects.filter(category_id__in=cat_ids, is_available=True)[:n]
        else:
            dishes = Dish.objects.filter(is_available=True)[:n]
        
        season = season_names.get(month, 'Сезонные')
        
        result = []
        for dish in dishes:
            result.append({
                'id': dish.id,
                'name': dish.name,
                'price': float(dish.price),
                'category_id': dish.category_id
            })
        
        return {
            'season': season,
            'recommendations': result
        }
    
    def save(self, path='ml/models/recommender.pkl'):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        print(f"✅ Модель сохранена в {path}")
    
    @classmethod
    def load(cls, path='ml/models/recommender.pkl'):
        with open(path, 'rb') as f:
            return pickle.load(f)