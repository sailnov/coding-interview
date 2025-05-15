# tests/api/test_category.py
from uuid import uuid4

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.company import Company
from api.models.category import Category


class CategoryAPITest(APITestCase):
    def setUp(self):
        # テスト用 Company を２つ用意
        self.company = Company.objects.create(name='Test社')
        self.other_company = Company.objects.create(name='Other社')
        # テスト用 Category を１つ作成
        self.parent = Category.objects.create(
            company=self.company, name='親カテゴリ')
        # URL
        self.list_url = reverse('category-list')
        self.detail_url = lambda pk: reverse('category-detail', args=[pk])

    # 正常系 ------------------------------------------------------------------

    def test_list_categories(self):
        """GET /categories/ → 200, list を返す"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_category(self):
        """GET /categories/{id}/ → 200, 該当データ"""
        response = self.client.get(self.detail_url(self.parent.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.parent.id))

    def test_create_category(self):
        """POST /categories/ → 201, 新規作成"""
        payload = {
            'company': str(self.company.id),
            'name': '新規カテゴリ',
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Category.objects.filter(
                company=self.company, name='新規カテゴリ').exists()
        )

    def test_create_with_parent_category(self):
        """親カテゴリ付きで作成 → 201, parent_category がセットされる"""
        payload = {
            'company': str(self.company.id),
            'name': '子カテゴリ',
            'parent_category': str(self.parent.id),
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        child = Category.objects.get(name='子カテゴリ')
        self.assertEqual(child.parent_category.id, self.parent.id)

    def test_update_category(self):
        """PUT /categories/{id}/ → 200, 更新が反映される"""
        payload = {
            'company': str(self.company.id),
            'name': '親カテゴリ（更新）',
            'parent_category': None,
        }
        response = self.client.put(self.detail_url(
            self.parent.id), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.name, '親カテゴリ（更新）')

    def test_partial_update_category(self):
        """PATCH /categories/{id}/ → 200, 部分更新"""
        payload = {'name': '部分更新カテゴリ'}
        response = self.client.patch(self.detail_url(
            self.parent.id), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.name, '部分更新カテゴリ')

    def test_delete_category(self):
        """DELETE /categories/{id}/ → 204, 削除される"""
        response = self.client.delete(self.detail_url(self.parent.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=self.parent.id).exists())

    # 異常系 ------------------------------------------------------------------

    def test_retrieve_nonexistent_category(self):
        """存在しない ID への GET → 404"""
        response = self.client.get(self.detail_url(uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_category_missing_fields(self):
        """必須フィールド欠如 → 400"""
        response = self.client.post(
            self.list_url, {'company': str(self.company.id)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_create_category_duplicate_name(self):
        """同一 Company 内で name 重複 → 400"""
        payload = {
            'company': str(self.company.id),
            'name': self.parent.name,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # serializer 側で UniqueConstraint 違反時に non_field_errors または name に出る
        self.assertTrue(
            'non_field_errors' in response.data or 'name' in response.data
        )

    def test_create_with_invalid_parent(self):
        """存在しない親カテゴリ指定 → 400"""
        payload = {
            'company': str(self.company.id),
            'name': '不正な親指定',
            'parent_category': str(uuid4()),
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('parent_category', response.data)

    def test_update_category_invalid_company(self):
        """更新時に存在しない Company 指定 → 400"""
        payload = {
            'company': str(uuid4()),
            'name': '更新失敗カテゴリ',
        }
        response = self.client.put(self.detail_url(
            self.parent.id), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company', response.data)

    def test_delete_nonexistent_category(self):
        """存在しない ID への DELETE → 404"""
        response = self.client.delete(self.detail_url(uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
