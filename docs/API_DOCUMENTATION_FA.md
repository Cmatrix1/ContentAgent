# مستندات فنی API سرویس ContentAgent

## 📋 فهرست مطالب

1. [مقدمه](#1-مقدمه)
2. [احراز هویت](#2-احراز-هویت)
3. [مفاهیم اصلی](#3-مفاهیم-اصلی)
4. [مستندات API](#4-مستندات-api)
   - [پروژه‌ها (Projects)](#41-پروژه‌ها-projects)
   - [جستجو (Search)](#42-جستجو-search)
   - [محتوا (Content)](#43-محتوا-content)
   - [زیرنویس (Subtitles)](#44-زیرنویس-subtitles)
   - [واترمارک (Watermark)](#45-واترمارک-watermark)
   - [کپی‌رایتینگ (Copywriting)](#46-کپی‌رایتینگ-copywriting)
5. [نکات پردازش](#5-نکات-پردازش)
6. [نکات فنی](#6-نکات-فنی)

---

## 1. مقدمه

### هدف سرویس

ContentAgent یک سرویس بک‌اند مبتنی بر هوش مصنوعی است که از طریق REST API در دسترس قرار می‌گیرد. این سرویس برای تیم‌هایی طراحی شده که می‌خواهند محتوای ویدیویی از پلتفرم‌های مختلف را پردازش کرده و محتوای تبلیغاتی تولید کنند.

### موارد استفاده در سیستم CRM

- **دانلود و پردازش ویدیو**: دانلود خودکار ویدیو از YouTube، Instagram و LinkedIn
- **تولید زیرنویس**: استخراج متن گفتار از ویدیو با استفاده از Gemini AI
- **ترجمه زیرنویس**: ترجمه زیرنویس به زبان‌های مختلف (پیش‌فرض: فارسی)
- **تولید محتوای تبلیغاتی**: تولید عنوان، کپشن، هشتگ و متن فراخوان با AI
- **واترمارک**: اضافه کردن لوگو به ویدیو

### معماری کلی

```
┌─────────────────────────────────────────────────────────────────┐
│                         CRM System                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ContentAgent REST API                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────────┐ │
│  │ Project │→→│ Search  │→→│ Content │→→│ Subtitle/Watermark  │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────────────┘ │
│                              │                   │              │
│                              ▼                   ▼              │
│                    ┌─────────────────────────────────┐          │
│                    │      Copywriting (AI)           │          │
│                    └─────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │  Celery  │   │ Gemini   │   │   APIHUT     │
        │  Tasks   │   │   AI     │   │ Video API    │
        └──────────┘   └──────────┘   └──────────────┘
```

---

## 2. احراز هویت

### روش احراز هویت

این API از **Token Authentication** استفاده می‌کند. هر درخواست باید شامل هدر `Authorization` باشد.

### هدرهای الزامی

| هدر | مقدار | توضیحات |
|-----|-------|---------|
| `Authorization` | `Token <YOUR_TOKEN>` | توکن احراز هویت |
| `Content-Type` | `application/json` | نوع محتوای درخواست |

### نمونه درخواست

```bash
curl -X GET "https://api.example.com/api/projects/" \
  -H "Authorization: Token abc123def456..." \
  -H "Content-Type: application/json"
```

### پاسخ‌های خطای احراز هویت

| کد وضعیت | توضیحات |
|----------|---------|
| `401 Unauthorized` | توکن ارائه نشده یا نامعتبر است |
| `403 Forbidden` | کاربر دسترسی به این منبع را ندارد |

**نمونه خطا:**

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## 3. مفاهیم اصلی

### 3.1 پروژه (Project) چیست؟

پروژه یک کانتینر اصلی برای سازماندهی کار شماست. هر پروژه می‌تواند شامل موارد زیر باشد:
- یک یا چند درخواست جستجو (Search Request)
- یک محتوا (Content)
- چندین زیرنویس
- چندین جلسه کپی‌رایتینگ

**فیلدهای پروژه:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `id` | UUID | شناسه یکتا |
| `title` | string | عنوان پروژه |
| `type` | string | نوع: `video` یا `text` |
| `status` | string | وضعیت: `draft`, `searching`, `selecting`, `generating`, `ready`, `published`, `failed` |
| `created_at` | datetime | تاریخ ایجاد |
| `updated_at` | datetime | تاریخ آخرین به‌روزرسانی |

### 3.2 محتوا (Content) چیست؟

محتوا یک ویدیو یا متن است که از نتایج جستجو انتخاب شده. هر پروژه فقط **یک محتوا** می‌تواند داشته باشد (رابطه One-to-One).

**فیلدهای محتوا:**

| فیلد | نوع | توضیحات |
|------|-----|---------|
| `id` | UUID | شناسه یکتا |
| `source_url` | URL | آدرس منبع ویدیو |
| `content_type` | string | نوع: `video`, `text`, `image` |
| `platform` | string | پلتفرم: `youtube`, `instagram`, `linkedin`, `other` |
| `file_path` | string | مسیر فایل دانلود شده (در صورت دانلود) |
| `download_status` | object | وضعیت دانلود ویدیو |

### 3.3 رابطه بین Project و Content

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Project    │──1:N─→│SearchRequest │──1:N─→│ SearchResult │
└──────────────┘       └──────────────┘       └──────────────┘
       │                                              │
       │                                              │
       └────────────────1:1───────────────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   Content    │
                  └──────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────────┐
    │ Subtitle │  │Watermark │  │ Copywriting  │
    │  (1:N)   │  │  (1:N)   │  │   Session    │
    └──────────┘  └──────────┘  └──────────────┘
```

### 3.4 چرخه حیات پردازش ویدیو

```
1. ایجاد پروژه                          [Project Created]
        │
        ▼
2. ایجاد درخواست جستجو                  [Search Started]
        │
        ▼
3. دریافت نتایج جستجو                   [Results Ready]
        │
        ▼
4. انتخاب یک نتیجه و ایجاد محتوا        [Content Created]
        │
        ▼
5. دانلود خودکار ویدیو                  [Video Downloaded]
        │
        ▼
6. تولید زیرنویس                        [Subtitle Generated]
        │
        ▼
7. ترجمه زیرنویس (اختیاری)              [Subtitle Translated]
        │
        ▼
8. حک زیرنویس روی ویدیو (اختیاری)       [Subtitle Burned]
        │
        ▼
9. اضافه کردن واترمارک (اختیاری)        [Watermark Added]
        │
        ▼
10. تولید محتوای تبلیغاتی               [Copywriting Generated]
```

---

## 4. مستندات API

### Base URL

```
https://your-domain.com/api/
```

---

### 4.1 پروژه‌ها (Projects)

#### 4.1.1 لیست پروژه‌ها

دریافت لیست تمام پروژه‌های کاربر.

| | |
|---|---|
| **Endpoint** | `GET /api/projects/` |
| **Method** | GET |
| **Authentication** | الزامی |

**هدرهای الزامی:**

```
Authorization: Token <YOUR_TOKEN>
```

**نمونه درخواست:**

```bash
curl -X GET "https://api.example.com/api/projects/" \
  -H "Authorization: Token abc123..."
```

**نمونه پاسخ موفق (200):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "owner": 1,
    "title": "پروژه ویدیوی آموزشی",
    "type": "video",
    "status": "draft",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

#### 4.1.2 ایجاد پروژه جدید

ایجاد یک پروژه جدید برای کاربر.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/` |
| **Method** | POST |
| **Authentication** | الزامی |

**بدنه درخواست (Request Body):**

| فیلد | نوع | الزامی | توضیحات |
|------|-----|--------|---------|
| `title` | string | ✅ | عنوان پروژه |
| `type` | string | ❌ | نوع پروژه: `video` یا `text` (پیش‌فرض: `text`) |

**نمونه درخواست:**

```bash
curl -X POST "https://api.example.com/api/projects/" \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "پروژه ویدیوی جدید",
    "type": "video"
  }'
```

**نمونه پاسخ موفق (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "owner": 1,
  "title": "پروژه ویدیوی جدید",
  "type": "video",
  "status": "draft",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**کدهای وضعیت:**

| کد | توضیحات |
|----|---------|
| `201` | پروژه با موفقیت ایجاد شد |
| `400` | داده‌های ارسالی نامعتبر است |
| `401` | احراز هویت ناموفق |

---

#### 4.1.3 حذف پروژه

حذف یک پروژه به همراه تمام داده‌های مرتبط.

| | |
|---|---|
| **Endpoint** | `DELETE /api/projects/{project_id}/` |
| **Method** | DELETE |
| **Authentication** | الزامی |

**پارامترهای مسیر:**

| پارامتر | نوع | توضیحات |
|---------|-----|---------|
| `project_id` | UUID | شناسه پروژه |

**نمونه درخواست:**

```bash
curl -X DELETE "https://api.example.com/api/projects/550e8400-e29b-41d4-a716-446655440000/" \
  -H "Authorization: Token abc123..."
```

**کدهای وضعیت:**

| کد | توضیحات |
|----|---------|
| `204` | پروژه با موفقیت حذف شد |
| `401` | احراز هویت ناموفق |
| `404` | پروژه یافت نشد یا دسترسی ندارید |

---

### 4.2 جستجو (Search)

#### 4.2.1 ایجاد درخواست جستجو

جستجو در پلتفرم‌های مختلف برای یافتن محتوای مرتبط. جستجو **به صورت همزمان (Synchronous)** انجام می‌شود.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/search-requests/` |
| **Method** | POST |
| **Authentication** | الزامی |

**پارامترهای مسیر:**

| پارامتر | نوع | توضیحات |
|---------|-----|---------|
| `project_id` | UUID | شناسه پروژه |

**بدنه درخواست:**

| فیلد | نوع | الزامی | پیش‌فرض | توضیحات |
|------|-----|--------|---------|---------|
| `query` | string | ✅ | - | عبارت جستجو |
| `language` | string | ❌ | `en` | زبان محتوا |
| `top_results_count` | integer | ❌ | `10` | تعداد نتایج |
| `platforms` | array | ❌ | همه پلتفرم‌ها | لیست پلتفرم‌ها: `youtube`, `instagram`, `linkedin` |
| `params` | object | ❌ | `{}` | پارامترهای اضافی |

**نمونه درخواست:**

```bash
curl -X POST "https://api.example.com/api/projects/550e8400.../search-requests/" \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "آموزش برنامه نویسی پایتون",
    "language": "fa",
    "top_results_count": 10,
    "platforms": ["youtube", "instagram"]
  }'
```

**نمونه پاسخ موفق (201):**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "query": "آموزش برنامه نویسی پایتون",
  "language": "fa",
  "top_results_count": 10,
  "platforms": ["youtube", "instagram"],
  "params": {},
  "status": "completed",
  "created_at": "2024-01-15T10:35:00Z",
  "completed_at": "2024-01-15T10:35:05Z"
}
```

**وضعیت‌های ممکن برای درخواست جستجو:**

| وضعیت | توضیحات |
|-------|---------|
| `pending` | در انتظار شروع |
| `in_progress` | در حال جستجو |
| `completed` | تکمیل شده |
| `failed` | با خطا مواجه شده |

---

#### 4.2.2 دریافت نتایج جستجو

دریافت لیست نتایج جستجوی یک پروژه.

| | |
|---|---|
| **Endpoint** | `GET /api/projects/{project_id}/search-results/` |
| **Method** | GET |
| **Authentication** | الزامی |

**پارامترهای Query:**

| پارامتر | نوع | پیش‌فرض | توضیحات |
|---------|-----|---------|---------|
| `only_selected` | boolean | `false` | فقط نتایج انتخاب‌شده |

**نمونه درخواست:**

```bash
curl -X GET "https://api.example.com/api/projects/550e8400.../search-results/?only_selected=true" \
  -H "Authorization: Token abc123..."
```

**نمونه پاسخ موفق (200):**

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "search_request": "660e8400-e29b-41d4-a716-446655440000",
    "title": "آموزش کامل پایتون از صفر تا صد",
    "link": "https://www.youtube.com/watch?v=abc123",
    "snippet": "در این ویدیو آموزش کامل پایتون را یاد می‌گیرید...",
    "rank": 1,
    "is_selected": false,
    "metadata": {
      "pagemap": {
        "metatags": [{"og:title": "آموزش پایتون"}]
      }
    },
    "fetched_at": "2024-01-15T10:35:05Z"
  }
]
```

---

### 4.3 محتوا (Content)

#### 4.3.1 ایجاد محتوا از نتیجه جستجو

انتخاب یک نتیجه جستجو و ایجاد محتوا برای پروژه. اگر محتوا ویدیو باشد، دانلود **به صورت غیرهمزمان** شروع می‌شود.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/content/create/` |
| **Method** | POST |
| **Authentication** | الزامی |

**بدنه درخواست:**

| فیلد | نوع | الزامی | توضیحات |
|------|-----|--------|---------|
| `search_result_id` | UUID | ✅ | شناسه نتیجه جستجوی انتخاب‌شده |

**نمونه درخواست:**

```bash
curl -X POST "https://api.example.com/api/projects/550e8400.../content/create/" \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "search_result_id": "770e8400-e29b-41d4-a716-446655440000"
  }'
```

**نمونه پاسخ موفق (201):**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "project_title": "پروژه ویدیوی جدید",
  "source_url": "https://www.youtube.com/watch?v=abc123",
  "content_type": "video",
  "platform": "youtube",
  "file_path": null,
  "download_status": {
    "task_id": "aa0e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "progress": 0,
    "error_message": null
  },
  "video_url": null,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

**کدهای خطا:**

| کد | توضیحات |
|----|---------|
| `400` | محتوا قبلاً برای این پروژه ایجاد شده / نتیجه جستجو متعلق به این پروژه نیست |
| `404` | پروژه یا نتیجه جستجو یافت نشد |

---

#### 4.3.2 دریافت محتوای پروژه

دریافت اطلاعات محتوای یک پروژه.

| | |
|---|---|
| **Endpoint** | `GET /api/projects/{project_id}/content/` |
| **Method** | GET |
| **Authentication** | الزامی |

**نمونه پاسخ موفق (200):**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "project_title": "پروژه ویدیوی جدید",
  "source_url": "https://www.youtube.com/watch?v=abc123",
  "content_type": "video",
  "platform": "youtube",
  "file_path": "videos/990e8400-e29b-41d4-a716-446655440000.mp4",
  "download_status": {
    "task_id": "aa0e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": 100,
    "error_message": null
  },
  "video_url": "https://api.example.com/media/videos/990e8400....mp4",
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:05:00Z"
}
```

---

#### 4.3.3 بررسی وضعیت دانلود ویدیو

دریافت وضعیت جاری دانلود ویدیو.

| | |
|---|---|
| **Endpoint** | `GET /api/projects/{project_id}/content/download-status/` |
| **Method** | GET |
| **Authentication** | الزامی |

**نمونه پاسخ موفق (200):**

```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440000",
  "content": "990e8400-e29b-41d4-a716-446655440000",
  "content_url": "https://www.youtube.com/watch?v=abc123",
  "task_id": "celery-task-id-12345",
  "status": "downloading",
  "progress": 45,
  "error_message": null,
  "download_url": "https://api.service.com/download/abc123",
  "file_size": 15728640,
  "started_at": "2024-01-15T11:01:00Z",
  "completed_at": null,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:02:30Z"
}
```

**وضعیت‌های دانلود:**

| وضعیت | توضیحات |
|-------|---------|
| `pending` | در انتظار شروع |
| `downloading` | در حال دانلود |
| `processing` | در حال پردازش |
| `completed` | دانلود موفق |
| `failed` | دانلود ناموفق |

---

#### 4.3.4 حذف محتوا

حذف محتوا و تمام داده‌های مرتبط.

| | |
|---|---|
| **Endpoint** | `DELETE /api/projects/{project_id}/content/delete/` |
| **Method** | DELETE |
| **Authentication** | الزامی |

**کدهای وضعیت:**

| کد | توضیحات |
|----|---------|
| `204` | محتوا با موفقیت حذف شد |
| `404` | پروژه یا محتوا یافت نشد |

---

### 4.4 زیرنویس (Subtitles)

#### 4.4.1 تولید زیرنویس

شروع فرآیند تولید زیرنویس برای ویدیو با استفاده از Gemini AI. این عملیات **غیرهمزمان** است.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/subtitles/generate/` |
| **Method** | POST |
| **Authentication** | الزامی |

**⚠️ نکته مهم:**
- برای ویدیوهای Instagram و LinkedIn، ابتدا باید ویدیو دانلود شده باشد.
- برای ویدیوهای YouTube، نیازی به دانلود نیست.

**نمونه درخواست:**

```bash
curl -X POST "https://api.example.com/api/projects/550e8400.../subtitles/generate/" \
  -H "Authorization: Token abc123..."
```

**نمونه پاسخ موفق (201):**

```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440000",
  "content": "990e8400-e29b-41d4-a716-446655440000",
  "language": "original",
  "content_url": "https://www.youtube.com/watch?v=abc123",
  "platform": "youtube",
  "project_title": "پروژه ویدیوی جدید",
  "task_id": "celery-task-id-67890",
  "status": "pending",
  "subtitle_text": null,
  "error_message": null,
  "started_at": null,
  "completed_at": null,
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

**کدهای خطا:**

| کد | توضیحات |
|----|---------|
| `400` | محتوا ویدیو نیست / زیرنویس قبلاً وجود دارد / ویدیو دانلود نشده |
| `404` | پروژه یا محتوا یافت نشد |

---

#### 4.4.2 لیست زیرنویس‌ها

دریافت لیست تمام زیرنویس‌های یک محتوا.

| | |
|---|---|
| **Endpoint** | `GET /api/projects/{project_id}/subtitles/` |
| **Method** | GET |
| **Authentication** | الزامی |

**نمونه پاسخ موفق (200):**

```json
[
  {
    "id": "bb0e8400-e29b-41d4-a716-446655440000",
    "content": "990e8400-e29b-41d4-a716-446655440000",
    "language": "original",
    "status": "completed",
    "subtitle_text": "1\n00:00:00,000 --> 00:00:03,200\nسلام به همه...",
    "created_at": "2024-01-15T12:00:00Z"
  },
  {
    "id": "cc0e8400-e29b-41d4-a716-446655440000",
    "content": "990e8400-e29b-41d4-a716-446655440000",
    "language": "persian",
    "status": "completed",
    "subtitle_text": "1\n00:00:00,000 --> 00:00:03,200\nمتن ترجمه شده...",
    "created_at": "2024-01-15T12:05:00Z"
  }
]
```

---

#### 4.4.3 ترجمه زیرنویس

ترجمه زیرنویس به زبان دیگر. این عملیات **همزمان (Synchronous)** است.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/subtitles/translate/` |
| **Method** | POST |
| **Authentication** | الزامی |

**بدنه درخواست:**

| فیلد | نوع | الزامی | پیش‌فرض | توضیحات |
|------|-----|--------|---------|---------|
| `source_subtitle_id` | UUID | ✅ | - | شناسه زیرنویس مبدا |
| `target_language` | string | ❌ | `persian` | زبان مقصد |

**زبان‌های پشتیبانی شده:**

- `persian` (فارسی)
- `english` (انگلیسی)
- `spanish` (اسپانیایی)
- `french` (فرانسوی)
- و سایر زبان‌های رایج

**نمونه درخواست:**

```bash
curl -X POST "https://api.example.com/api/projects/550e8400.../subtitles/translate/" \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "source_subtitle_id": "bb0e8400-e29b-41d4-a716-446655440000",
    "target_language": "persian"
  }'
```

**نمونه پاسخ موفق (200):**

```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440000",
  "content": "990e8400-e29b-41d4-a716-446655440000",
  "language": "persian",
  "status": "completed",
  "subtitle_text": "1\n00:00:00,000 --> 00:00:03,000\nسلام به همه، خوش برگشتید!\n\n2\n00:00:03,000 --> 00:00:06,000\nامروز می‌خوام یه چیز جالب نشونتون بدم.",
  "started_at": "2024-01-15T13:00:00Z",
  "completed_at": "2024-01-15T13:00:15Z"
}
```

---

#### 4.4.4 حک زیرنویس روی ویدیو

حک (Burn) زیرنویس به صورت دائمی روی ویدیو با ffmpeg. این عملیات **غیرهمزمان** است.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/subtitles/{subtitle_id}/burn/` |
| **Method** | POST |
| **Authentication** | الزامی |

**پیش‌نیازها:**
- زیرنویس باید با وضعیت `completed` باشد
- ویدیو باید دانلود شده باشد

**نمونه پاسخ موفق (201):**

```json
{
  "id": "dd0e8400-e29b-41d4-a716-446655440000",
  "subtitle": "cc0e8400-e29b-41d4-a716-446655440000",
  "subtitle_language": "persian",
  "content_id": "990e8400-e29b-41d4-a716-446655440000",
  "task_id": "celery-task-id-99999",
  "status": "pending",
  "output_file_path": null,
  "error_message": null
}
```

---

#### 4.4.5 بررسی وضعیت حک زیرنویس

| | |
|---|---|
| **Endpoint** | `GET /api/projects/{project_id}/burn-tasks/{burn_task_id}/` |
| **Method** | GET |
| **Authentication** | الزامی |

**نمونه پاسخ موفق (200):**

```json
{
  "id": "dd0e8400-e29b-41d4-a716-446655440000",
  "subtitle": "cc0e8400-e29b-41d4-a716-446655440000",
  "subtitle_language": "persian",
  "content_id": "990e8400-e29b-41d4-a716-446655440000",
  "task_id": "celery-task-id-99999",
  "status": "completed",
  "output_file_path": "videos/subtitled/990e8400..._persian.mp4",
  "error_message": null,
  "completed_at": "2024-01-15T14:00:00Z"
}
```

---

#### 4.4.6 حذف زیرنویس

| | |
|---|---|
| **Endpoint** | `DELETE /api/projects/{project_id}/subtitles/{subtitle_id}/delete/` |
| **Method** | DELETE |
| **Authentication** | الزامی |

---

### 4.5 واترمارک (Watermark)

#### 4.5.1 اضافه کردن واترمارک

آپلود تصویر واترمارک و حک آن روی ویدیو. این عملیات **غیرهمزمان** است.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/watermark/` |
| **Method** | POST |
| **Authentication** | الزامی |
| **Content-Type** | `multipart/form-data` |

**بدنه درخواست:**

| فیلد | نوع | الزامی | توضیحات |
|------|-----|--------|---------|
| `watermark_image` | file | ✅ | فایل تصویر واترمارک (PNG با شفافیت توصیه می‌شود) |

**نمونه درخواست:**

```bash
curl -X POST "https://api.example.com/api/projects/550e8400.../watermark/" \
  -H "Authorization: Token abc123..." \
  -F "watermark_image=@logo.png"
```

**نمونه پاسخ موفق (201):**

```json
{
  "id": "ee0e8400-e29b-41d4-a716-446655440000",
  "content": "990e8400-e29b-41d4-a716-446655440000",
  "content_id": "990e8400-e29b-41d4-a716-446655440000",
  "watermark_image": "/media/watermarks/logo.png",
  "watermark_image_url": "https://api.example.com/media/watermarks/logo.png",
  "task_id": "celery-task-id-88888",
  "status": "pending",
  "output_file_path": null,
  "error_message": null
}
```

**📍 موقعیت واترمارک:** گوشه پایین سمت راست ویدیو (با ۱۰ پیکسل فاصله از لبه‌ها)

---

#### 4.5.2 بررسی وضعیت واترمارک

| | |
|---|---|
| **Endpoint** | `GET /api/projects/{project_id}/watermark-tasks/{watermark_task_id}/` |
| **Method** | GET |
| **Authentication** | الزامی |

---

### 4.6 کپی‌رایتینگ (Copywriting)

#### 4.6.1 تولید محتوای تبلیغاتی

تولید محتوای تبلیغاتی فارسی با استفاده از Gemini AI. این عملیات **همزمان** است.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/copywriting/generate/` |
| **Method** | POST |
| **Authentication** | الزامی |

**بدنه درخواست:**

| فیلد | نوع | الزامی | توضیحات |
|------|-----|--------|---------|
| `description` | string | ❌ | یادداشت یا توضیحات اضافی کاربر |

**نمونه درخواست:**

```bash
curl -X POST "https://api.example.com/api/projects/550e8400.../copywriting/generate/" \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "description": "محتوای جذاب و SEO-friendly تولید کن"
  }'
```

**نمونه پاسخ موفق (201):**

```json
{
  "id": "ff0e8400-e29b-41d4-a716-446655440000",
  "project": "550e8400-e29b-41d4-a716-446655440000",
  "inputs": {
    "title": "پروژه ویدیوی جدید",
    "platform": "youtube",
    "subtitle": "متن زیرنویس...",
    "subtitle_language": "persian",
    "user_description": "محتوای جذاب و SEO-friendly تولید کن"
  },
  "outputs": {
    "title": "🚀 آموزش کامل پایتون | از صفر تا حرفه‌ای",
    "caption": "می‌خوای برنامه‌نویسی یاد بگیری؟ 💻\n\nاین ویدیو تمام چیزی هست که نیاز داری...",
    "micro_caption": "آموزش پایتون از صفر 🐍",
    "meta_description": "آموزش کامل زبان برنامه‌نویسی پایتون برای مبتدیان و حرفه‌ای‌ها",
    "hashtags": ["#پایتون", "#برنامه_نویسی", "#آموزش", "#کدنویسی", "#python"],
    "cta": "همین الان شروع کن! 👇",
    "alt_text": "ویدیوی آموزش برنامه‌نویسی پایتون"
  },
  "edits": {},
  "final_outputs": {
    "title": "🚀 آموزش کامل پایتون | از صفر تا حرفه‌ای",
    "caption": "می‌خوای برنامه‌نویسی یاد بگیری؟ 💻\n\nاین ویدیو تمام چیزی هست که نیاز داری...",
    "micro_caption": "آموزش پایتون از صفر 🐍",
    "meta_description": "آموزش کامل زبان برنامه‌نویسی پایتون برای مبتدیان و حرفه‌ای‌ها",
    "hashtags": ["#پایتون", "#برنامه_نویسی", "#آموزش", "#کدنویسی", "#python"],
    "cta": "همین الان شروع کن! 👇",
    "alt_text": "ویدیوی آموزش برنامه‌نویسی پایتون"
  },
  "status": "pending",
  "created_at": "2024-01-15T15:00:00Z",
  "updated_at": "2024-01-15T15:00:00Z"
}
```

**فیلدهای خروجی AI:**

| فیلد | توضیحات |
|------|---------|
| `title` | عنوان جذاب |
| `caption` | کپشن کامل برای شبکه‌های اجتماعی |
| `micro_caption` | نسخه کوتاه کپشن |
| `meta_description` | توضیحات متا برای SEO |
| `hashtags` | لیست هشتگ‌ها |
| `cta` | متن فراخوان (Call to Action) |
| `alt_text` | متن جایگزین برای دسترس‌پذیری |

---

#### 4.6.2 دریافت جزئیات جلسه کپی‌رایتینگ

| | |
|---|---|
| **Endpoint** | `GET /api/projects/{project_id}/copywriting/{session_id}/` |
| **Method** | GET |
| **Authentication** | الزامی |

---

#### 4.6.3 ویرایش دستی یک بخش

ویرایش دستی یکی از بخش‌های محتوای تولیدشده.

| | |
|---|---|
| **Endpoint** | `PATCH /api/projects/{project_id}/copywriting/{session_id}/edit/` |
| **Method** | PATCH |
| **Authentication** | الزامی |

**بدنه درخواست:**

| فیلد | نوع | الزامی | توضیحات |
|------|-----|--------|---------|
| `section` | string | ✅ | نام بخش (مثل `title`, `caption`, `cta`) |
| `new_value` | string | ✅ | مقدار جدید |

**نمونه درخواست:**

```bash
curl -X PATCH "https://api.example.com/api/projects/550e8400.../copywriting/ff0e8400.../edit/" \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "section": "cta",
    "new_value": "همین الان دانلود کن! 🔥"
  }'
```

**نمونه پاسخ موفق (200):**

```json
{
  "message": "Section \"cta\" updated successfully.",
  "section": "cta",
  "new_value": "همین الان دانلود کن! 🔥"
}
```

---

#### 4.6.4 بازتولید یک بخش با AI

بازتولید یکی از بخش‌ها با دستورالعمل جدید.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/copywriting/{session_id}/regenerate/` |
| **Method** | POST |
| **Authentication** | الزامی |

**بدنه درخواست:**

| فیلد | نوع | الزامی | توضیحات |
|------|-----|--------|---------|
| `section` | string | ✅ | نام بخش |
| `instruction` | string | ✅ | دستورالعمل برای AI |

**نمونه درخواست:**

```bash
curl -X POST "https://api.example.com/api/projects/550e8400.../copywriting/ff0e8400.../regenerate/" \
  -H "Authorization: Token abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "section": "caption",
    "instruction": "کوتاه‌تر و خنده‌دارتر بنویس"
  }'
```

---

#### 4.6.5 ذخیره نهایی

نهایی کردن و ذخیره محتوای تولیدشده.

| | |
|---|---|
| **Endpoint** | `POST /api/projects/{project_id}/copywriting/{session_id}/save/` |
| **Method** | POST |
| **Authentication** | الزامی |

**نمونه پاسخ موفق (200):**

```json
{
  "message": "Copywriting saved successfully.",
  "status": "completed",
  "final_outputs": {
    "title": "🚀 آموزش کامل پایتون",
    "caption": "متن نهایی...",
    "cta": "همین الان دانلود کن! 🔥"
  }
}
```

---

## 5. نکات پردازش

### 5.1 عملیات همزمان و غیرهمزمان

| عملیات | نوع | توضیحات |
|--------|-----|---------|
| ایجاد پروژه | همزمان | فوری |
| جستجو | همزمان | ۵-۱۰ ثانیه |
| ایجاد محتوا | همزمان | فوری (دانلود غیرهمزمان شروع می‌شود) |
| **دانلود ویدیو** | **غیرهمزمان** | ۱-۵ دقیقه |
| **تولید زیرنویس** | **غیرهمزمان** | ۱-۳ دقیقه |
| ترجمه زیرنویس | همزمان | ۱۰-۳۰ ثانیه |
| **حک زیرنویس** | **غیرهمزمان** | ۱-۱۰ دقیقه |
| **واترمارک** | **غیرهمزمان** | ۱-۱۰ دقیقه |
| کپی‌رایتینگ | همزمان | ۱۰-۳۰ ثانیه |

### 5.2 بررسی وضعیت عملیات غیرهمزمان

برای عملیات‌های غیرهمزمان، باید به صورت دوره‌ای وضعیت را بررسی کنید (Polling):

```python
import time
import requests

def wait_for_download(api_url, token, project_id, max_wait=300):
    """منتظر تکمیل دانلود بماند"""
    headers = {"Authorization": f"Token {token}"}
    endpoint = f"{api_url}/api/projects/{project_id}/content/download-status/"
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(endpoint, headers=headers)
        data = response.json()
        
        if data["status"] == "completed":
            return True, data
        elif data["status"] == "failed":
            return False, data
        
        time.sleep(5)  # هر ۵ ثانیه بررسی کن
    
    return False, {"error": "Timeout"}
```

### 5.3 توصیه فاصله زمانی Polling

| عملیات | فاصله پیشنهادی | حداکثر انتظار |
|--------|----------------|---------------|
| دانلود ویدیو | ۵ ثانیه | ۵ دقیقه |
| تولید زیرنویس | ۱۰ ثانیه | ۵ دقیقه |
| حک زیرنویس | ۱۰ ثانیه | ۱۰ دقیقه |
| واترمارک | ۱۰ ثانیه | ۱۰ دقیقه |

### 5.4 Idempotency

- **ایجاد محتوا**: یک پروژه فقط می‌تواند یک محتوا داشته باشد. درخواست مجدد خطای `400` برمی‌گرداند.
- **تولید زیرنویس**: اگر زیرنویس وجود داشته باشد، خطا برمی‌گردد. برای بازتولید، ابتدا باید زیرنویس را حذف کنید.
- **ترجمه زیرنویس**: اگر ترجمه وجود داشته باشد (و خطا نخورده باشد)، خطا برمی‌گردد.

---

## 6. نکات فنی

### 6.1 محدودیت نرخ درخواست (Rate Limiting)

| نوع کاربر | محدودیت |
|-----------|---------|
| کاربر احراز هویت نشده | ۱۰۰ درخواست در ساعت |
| کاربر احراز هویت شده | ۱۰۰۰ درخواست در ساعت |

**هدرهای Rate Limit:**

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642345678
```

### 6.2 محدودیت‌های فایل

| نوع | محدودیت |
|-----|---------|
| حداکثر مدت ویدیو | بدون محدودیت رسمی (توصیه: زیر ۳۰ دقیقه) |
| حداکثر حجم ویدیو | بستگی به پلتفرم منبع |
| فرمت واترمارک | PNG, JPG, WEBP (PNG با شفافیت توصیه می‌شود) |

### 6.3 پلتفرم‌های پشتیبانی شده

| پلتفرم | دانلود | زیرنویس | توضیحات |
|--------|--------|---------|---------|
| YouTube | ✅ | ✅ | زیرنویس بدون نیاز به دانلود |
| Instagram | ✅ | ✅ | فقط Reels پشتیبانی می‌شود |
| LinkedIn | ✅ | ✅ | نیاز به yt-dlp |

### 6.4 فرمت زیرنویس

زیرنویس‌ها در فرمت **SRT** تولید می‌شوند:

```srt
1
00:00:00,000 --> 00:00:03,200
سلام به همه، خوش برگشتید!

2
00:00:03,200 --> 00:00:06,800
امروز می‌خوام یه چیز جالب نشونتون بدم.
```

### 6.5 کدهای خطای عمومی

| کد | معنی |
|----|------|
| `400 Bad Request` | داده‌های ارسالی نامعتبر است |
| `401 Unauthorized` | توکن نامعتبر یا ارائه نشده |
| `403 Forbidden` | دسترسی به این منبع ندارید |
| `404 Not Found` | منبع یافت نشد |
| `429 Too Many Requests` | از حد مجاز درخواست فراتر رفته‌اید |
| `500 Internal Server Error` | خطای داخلی سرور |

### 6.6 مستندات Swagger

مستندات تعاملی API در آدرس‌های زیر در دسترس است:

- **Swagger UI:** `/api/docs/`
- **ReDoc:** `/api/redoc/`
- **OpenAPI Schema:** `/api/schema/`

---

## نویسنده و نسخه

- **نسخه مستندات:** 1.0.0
- **تاریخ:** دسامبر ۲۰۲۴
- **API Version:** 1.0.0

---

*این مستندات بر اساس تحلیل کد منبع پروژه ContentAgent تولید شده است.*

