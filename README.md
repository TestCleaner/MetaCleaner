# MetaCleaner

Инструмент для **очистки метаданных** и **сжатия медиафайлов** в проектах любого типа (Flutter, iOS, Android, веб) и обычных папках с фото/видео.

MetaCleaner рекурсивно обходит директорию, находит изображения и видео по расширению, удаляет метаданные (EXIF, GPS, XMP, теги контейнера) и сжимает файлы без заметной потери качества.

> **Важно:** файлы заменяются **на месте**, без создания бэкапов.
> Перед первым запуском используйте `--dry-run` или сделайте `git commit`.

---

## Содержание

- [Что делает инструмент](#что-делает-инструмент)
- [Поддерживаемые форматы](#поддерживаемые-форматы)
- [Установка (локальная)](#установка-локальная)
- [Быстрый старт](#быстрый-старт)
- [Команды и флаги](#команды-и-флаги)
- [Конфигурация (.metacleaner.yaml)](#конфигурация-metacleaneryaml)
- [Автоматизация в GitHub Actions](#автоматизация-в-github-actions)
  - [Для одного репозитория](#для-одного-репозитория)
  - [Для всей организации](#для-всей-организации)
- [Файлы проекта — что зачем](#файлы-проекта--что-зачем)
- [Как обрабатывается каждый формат](#как-обрабатывается-каждый-формат)
- [Поведение и безопасность](#поведение-и-безопасность)
- [Коды выхода](#коды-выхода)
- [Устранение проблем](#устранение-проблем)

---

## Что делает инструмент

1. **Один проход** по папке — быстрый рекурсивный обход с пропуском служебных директорий (`node_modules`, `build`, `.git`, `Pods` и др.)
2. **Очистка метаданных** — EXIF, GPS, IPTC, XMP, теги контейнера видео
3. **Сжатие** — уменьшение размера файла при визуально приемлемом качестве
4. **Замена на месте** — оптимизированный файл подменяет оригинал
5. **Защита от увеличения** — если результат не меньше оригинала, файл не трогается
6. **Пропуск иконок приложений** — launcher icons (AppIcon, mipmap, ic_launcher) не сжимаются

Аудиофайлы (`.mp3`, `.wav`, `.flac` и т.д.) **не обрабатываются**.

---

## Поддерживаемые форматы

### Изображения
| Расширение | Описание |
|------------|----------|
| `.jpg`, `.jpeg` | Фотографии |
| `.png` | Растровые изображения, иконки |
| `.webp` | WebP |
| `.heic`, `.heif` | Apple HEIC (конвертируется в JPEG) |

### Вектор
| Расширение | Описание |
|------------|----------|
| `.svg` | SVG-иконки и иллюстрации |

### Видео
| Расширение | Описание |
|------------|----------|
| `.mp4` | MP4 (H.264) |
| `.mov` | QuickTime |
| `.m4v` | MPEG-4 Video |
| `.webm` | WebM (VP9) |
| `.mkv` | Matroska |

---

## Установка (локальная)

Локальная установка нужна **только для запуска вручную**. Для автоматизации через CI ничего на машину ставить не нужно.

### Требования

- **Python 3.10+**
- Внешние утилиты (устанавливаются один раз)

### macOS (Homebrew)

```bash
brew install exiftool ffmpeg mozjpeg pngquant webp svgo oxipng

git clone https://github.com/[ВАШ_ОРГ]/[ИМЯ_РЕПО_METACLEANER].git MetaCleaner
cd MetaCleaner
python3 -m pip install -r requirements.txt
chmod +x metacleaner.sh
```

### Linux (Debian/Ubuntu)

```bash
sudo apt install libimage-exiftool-perl ffmpeg pngquant webp svgo oxipng libjpeg-turbo-progs libheif-examples

git clone https://github.com/[ВАШ_ОРГ]/[ИМЯ_РЕПО_METACLEANER].git MetaCleaner
cd MetaCleaner
python3 -m pip install -r requirements.txt
chmod +x metacleaner.sh
```

### Проверка зависимостей

```bash
./metacleaner.sh --doctor .
```

Покажет установленные и отсутствующие утилиты. Для обработки нужны только те, форматы которых реально есть в папке.

---

## Быстрый старт

```bash
# 1. Превью — ничего не меняет
./metacleaner.sh /path/to/folder --dry-run --verbose

# 2. Применить
./metacleaner.sh /path/to/folder -j 8
```

Работает как с проектом, так и с обычной папкой медиа.

---

## Команды и флаги

```
./metacleaner.sh <путь> [опции]
```

| Флаг | Описание |
|------|----------|
| `<путь>` | Папка для обработки (обязательный) |
| `--dry-run` | Показать, что будет обработано, без изменений |
| `--verbose` | Выводить статус каждого файла |
| `-j`, `--jobs N` | Параллельных потоков (по умолчанию: 4) |
| `--images-only` | Только изображения и SVG |
| `--videos-only` | Только видео |
| `--config FILE` | Путь к YAML-конфигу |
| `--json` | Отчёт в формате JSON |
| `--check` | Exit code 1, если найдены медиафайлы для обработки |
| `--strict` | Exit code 1, если хотя бы один файл не удалось обработать |
| `--doctor` | Проверить установленные зависимости |
| `--files FILE ...` | Обработать только указанные файлы |

---

## Конфигурация (.metacleaner.yaml)

### Нужен ли этот файл?

**Нет, не обязательно.** Без конфига MetaCleaner работает с разумными значениями по умолчанию. Файл нужен, только если вы хотите изменить качество сжатия, исключить определённые папки или отключить защиту иконок.

### Как создать

Скопируйте пример в корень вашего проекта:

```bash
cp metacleaner.yaml.example /path/to/project/.metacleaner.yaml
```

MetaCleaner ищет конфиг в порядке:
1. Путь из `--config`
2. `.metacleaner.yaml` в корне обрабатываемой папки
3. `metacleaner.yaml` в корне обрабатываемой папки

### Все параметры

```yaml
# Качество JPEG (MozJPEG / libjpeg-turbo)
jpeg_quality: 85

# PNG: диапазон качества pngquant ("мин-макс")
png_quality: "92-100"
png_speed: 1          # 1 = лучшее качество, 11 = быстрее
png_lossless: false   # true = oxipng без потерь (нужен oxipng)

# WebP
webp_quality: 80

# Видео H.264 (mp4, mov, m4v, mkv)
video_crf: 24         # 18–28: меньше = лучше качество
video_preset: fast    # ultrafast … veryslow

# WebM (VP9)
video_webm_cpu_used: 2  # 0 = лучше качество, 5 = быстрее

# Общие
strip_metadata: true   # удалять метаданные
skip_if_larger: true   # не заменять, если результат больше оригинала
skip_app_icons: true   # не сжимать launcher icons (AppIcon, mipmap, ic_launcher и т.д.)
subprocess_timeout: 300

# Папки, которые полностью пропускаются
exclude_dirs:
  - .git
  - node_modules
  - build
  - dist
  - out
  - .dart_tool
  - Pods
  - DerivedData
  - .gradle
  - vendor
  - __pycache__
  - .idea
  - .vscode
  - Carthage

# Glob-паттерны для исключения файлов
exclude_globs:
  - "**/test/**"
  - "**/tests/**"
  - "**/fixtures/**"

# Какие расширения обрабатывать
extensions:
  images: [.jpg, .jpeg, .png, .webp, .heic, .heif]
  svg: [.svg]
  videos: [.mp4, .mov, .m4v, .webm, .mkv]
```

### Важно: `exclude_dirs` заменяет список целиком

Если вы указываете `exclude_dirs` в конфиге, он **перезаписывает** весь список по умолчанию. Если нужно добавить свою папку — копируйте весь список из примера и добавьте к нему.

### skip_app_icons

По умолчанию включено. Автоматически пропускает:
- iOS/macOS: `*.appiconset`, `*.launchimage`, `AppIcon/`
- Android: `mipmap-*`, `ic_launcher*`, `ic_launcher_foreground/background`
- Flutter / RN / PWA: `Icon-App-*`, `favicon*`, `apple-touch-icon*`, `playstore-icon*`

Свои исключения — через `exclude_globs`. Отключить: `skip_app_icons: false`.

---

## Автоматизация в GitHub Actions

MetaCleaner можно подключить к CI: при PR с медиафайлами бот автоматически сжимает их и коммитит в ту же ветку.

```
Разработчик: push → открывает PR с photo.png
       ↓
GitHub Actions (ubuntu-latest)
       ↓
MetaCleaner обрабатывает только изменённые медиа
       ↓
Коммит от github-actions[bot] в ветку PR
```

Разработчикам **ничего не нужно ставить локально**.

---

### Предварительные требования

1. **Репозиторий MetaCleaner** опубликован в вашей GitHub-организации (или доступен публично)
2. Репозиторий MetaCleaner **public** — иначе reusable workflow не будет доступен из других репо (на free-плане GitHub нет org secrets для private cross-repo доступа)
3. На ветке `main` репозитория MetaCleaner — актуальный код

---

### Для одного репозитория

#### Шаг 1. Создайте файл workflow

В вашем проекте создайте `.github/workflows/optimize-media.yml`:

```yaml
name: Optimize media

on:
  pull_request:
    types: [opened, synchronize, reopened]
    paths:
      - '**.jpg'
      - '**.jpeg'
      - '**.png'
      - '**.webp'
      - '**.heic'
      - '**.heif'
      - '**.svg'
      - '**.mp4'
      - '**.mov'
      - '**.m4v'
      - '**.webm'
      - '**.mkv'

concurrency:
  group: optimize-media-${{ github.head_ref }}
  cancel-in-progress: true

jobs:
  optimize:
    if: github.actor != 'github-actions[bot]'
    uses: [ВАШ_ОРГ]/[ИМЯ_РЕПО_METACLEANER]/.github/workflows/optimize-media.yml@main
    permissions:
      contents: write
    with:
      metacleaner_repository: '[ВАШ_ОРГ]/[ИМЯ_РЕПО_METACLEANER]'
      metacleaner_ref: main
      process_videos: true
      commit_message: 'chore: optimize media assets'
```

Замените `[ВАШ_ОРГ]` на имя вашей GitHub-организации, `[ИМЯ_РЕПО_METACLEANER]` на имя репозитория с MetaCleaner (например `MetaCleaner`).

#### Шаг 2. Добавьте .gitignore (рекомендуется)

В корне проекта добавьте в `.gitignore`:

```gitignore
# MetaCleaner CI (артефакты раннера, не должны попадать в коммит)
.ci/
.metacleaner-tool/
*.metacleaner.tmp*
```

Это страховка: workflow не должен коммитить эти файлы, но gitignore предотвращает случайный `git add .`.

#### Шаг 3. (Опционально) Добавьте .metacleaner.yaml

Если нужны свои настройки (качество, exclude_dirs, skip_app_icons):

```bash
cp metacleaner.yaml.example /path/to/project/.metacleaner.yaml
```

**Без этого файла** MetaCleaner работает с дефолтами — для большинства проектов этого достаточно.

#### Шаг 4. Закоммитьте и проверьте

```bash
git add .github/workflows/optimize-media.yml .gitignore
git commit -m "chore: add MetaCleaner media optimization"
git push
```

Откройте PR, в котором изменён или добавлен медиафайл (jpg, png, mp4 и т.д.). Во вкладке **Actions** должен появиться workflow **Optimize media**.

---

### Для всей организации

Скрипт `scripts/install-org-workflow.sh` автоматически создаёт PR с workflow в каждом репозитории организации.

#### Шаг 1. Установите GitHub CLI

```bash
# macOS
brew install gh

# Linux
sudo apt install gh
# или: https://cli.github.com/
```

#### Шаг 2. Авторизуйтесь

```bash
gh auth login
```

Выберите: GitHub.com → HTTPS → Login with a web browser.

Ваш аккаунт должен иметь **admin-доступ** к репозиториям организации.

#### Шаг 3. Превью (без изменений)

```bash
cd /path/to/MetaCleaner
./scripts/install-org-workflow.sh [ВАШ_ОРГ] [ИМЯ_РЕПО_METACLEANER] --dry-run
```

Скрипт покажет список всех репозиториев org, в которые будет добавлен workflow. Ничего не изменит.

#### Шаг 4. Раскатка

```bash
./scripts/install-org-workflow.sh [ВАШ_ОРГ] [ИМЯ_РЕПО_METACLEANER]
```

Что скрипт делает **в каждом репозитории**:
1. Клонирует (shallow)
2. Создаёт ветку `chore/add-metacleaner-workflow`
3. Добавляет `.github/workflows/optimize-media.yml`
4. Дописывает `.ci/` и `.metacleaner-tool/` в `.gitignore`
5. Открывает **Pull Request**

#### Шаг 5. Смержите PR

Скрипт **не мержит автоматически** — зайдите в PR каждого репо и нажмите Merge (или через `gh pr merge`).

После merge workflow становится активным: любой PR с медиафайлами запускает оптимизацию.

---

### Параметры caller workflow

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `metacleaner_repository` | Org/Repo с MetaCleaner | — (обязательный) |
| `metacleaner_ref` | Ветка/тег MetaCleaner | `main` |
| `process_videos` | Обрабатывать видео | `true` |
| `commit_message` | Сообщение коммита бота | `chore: optimize media assets` |

Для фиксации версии замените `@main` на `@v1.0.0` или SHA коммита.

---

### Ограничения CI

| Ситуация | Поведение |
|----------|-----------|
| PR из fork внешнего контрибутора | auto-commit **не работает** (ограничение GitHub) |
| PR внутри org | работает |
| Большие видео | job может идти долго; отключите: `process_videos: false` |
| Повторный push от бота | пропускается (`if: github.actor != 'github-actions[bot]'`) |

---

### Обновление MetaCleaner для всех проектов

Все проекты ссылаются на `@main` репозитория MetaCleaner. Обновили MetaCleaner → все проекты используют новую версию автоматически.

---

## Файлы проекта — что зачем

### Что лежит в репозитории MetaCleaner

| Файл / Папка | Назначение |
|--------------|------------|
| `metacleaner.sh` | Точка входа для локального запуска |
| `metacleaner/` | Python-код CLI (config, walker, handlers, report) |
| `.github/workflows/optimize-media.yml` | Reusable workflow — вся логика CI |
| `templates/caller-workflow.yml` | Шаблон для проектов (с плейсхолдерами `@ORG@`, `@METACLEANER@`) |
| `templates/metacleaner-gitignore` | Строки для `.gitignore` проектов (добавляются скриптом) |
| `scripts/install-org-workflow.sh` | Раскатка workflow по всей org |
| `metacleaner.yaml.example` | Пример конфига со всеми параметрами |
| `requirements.txt` | Python-зависимости (PyYAML) |

### Что нужно добавить в ваш проект (минимум для CI)

| Файл | Обязателен | Назначение |
|------|------------|------------|
| `.github/workflows/optimize-media.yml` | **Да** | Вызывает MetaCleaner на PR с медиа |
| `.gitignore` (строки `.ci/`, `.metacleaner-tool/`, `*.metacleaner.tmp*`) | Рекомендуется | Не даёт CI-артефактам попасть в git |
| `.metacleaner.yaml` | Нет | Только если нужны свои настройки |

### Что в .gitignore для MetaCleaner

```gitignore
# MetaCleaner CI
.ci/                    # apt-кэш раннера (если workflow вдруг создаст его в repo)
.metacleaner-tool/      # checkout MetaCleaner на раннере (не часть вашего проекта)
*.metacleaner.tmp*      # временные файлы при обработке
```

Эти строки — **страховка**. Workflow коммитит только медиафайлы, но gitignore предотвращает случайности.

### Что в .metacleaner.yaml

Конфиг MetaCleaner для вашего проекта. Содержит настройки качества сжатия, списки исключений и расширения. **Без него всё работает на дефолтах.** Нужен, если:

- Хотите изменить `jpeg_quality`, `video_crf` и т.д.
- Нужно исключить папки помимо стандартных (`exclude_dirs`)
- Хотите отключить `skip_app_icons`
- Нужно добавить свои `exclude_globs` (например `**/brand/**`)

---

## Как обрабатывается каждый формат

| Формат | Инструмент | Действие |
|--------|------------|----------|
| JPEG | cjpeg/djpeg (mozjpeg или libjpeg-turbo) | Пересжатие + удаление EXIF |
| PNG | pngquant / oxipng | Lossy-сжатие с палитрой или lossless |
| WebP | cwebp | Сжатие + `-metadata none` |
| HEIC | heif-convert → FFmpeg (fallback) | Конвертация в JPEG + strip metadata |
| SVG | svgo | Минификация + очистка editor metadata |
| MP4/MOV/M4V | FFmpeg libx264 | CRF-сжатие + strip metadata + faststart |
| MKV | FFmpeg libx264 | CRF-сжатие + strip metadata |
| WebM | FFmpeg libvpx-vp9 | VP9-сжатие + strip metadata |

---

## Поведение и безопасность

- Файлы **заменяются на месте** — бэкапы не создаются
- Рекомендуется перед первым запуском: `--dry-run` или `git commit`
- Если результат **больше или равен** оригиналу — оригинал сохраняется (`skip_if_larger: true`)
- HEIC конвертируется в `.jpg` — исходный `.heic` удаляется
- Временные файлы (`*.metacleaner.tmp*`) создаются рядом и удаляются после
- Служебные папки (`build`, `.git`, `node_modules`, `Pods` и др.) пропускаются автоматически
- Иконки приложений (AppIcon, mipmap, ic_launcher) **не сжимаются** по умолчанию

---

## Коды выхода

| Код | Значение |
|-----|----------|
| `0` | Успех (хотя бы один файл оптимизирован, или нет медиа) |
| `1` | Ошибки: `--doctor` — нет зависимостей; `--check` — найдены медиа; `--strict` — не все файлы обработаны |
| `2` | Ошибка аргументов или путь не является папкой |

---

## Устранение проблем

### `missing required tools: mozjpeg (cjpeg/djpeg)`

На Ubuntu `mozjpeg` часто недоступен в apt. Установите `libjpeg-turbo-progs`:

```bash
sudo apt install libjpeg-turbo-progs
```

На macOS: `brew install mozjpeg`.

### Артефакты (полосы) в градиентах PNG

Поднимите `png_quality` до `"95-100"` или включите `png_lossless: true` (нужен `oxipng`).

### Ошибка WebM: `Only VP8 or VP9 or AV1...`

WebM не поддерживает H.264. MetaCleaner автоматически использует VP9 для `.webm`.

### Ошибка FFmpeg: `Unable to choose an output format`

Убедитесь, что используете актуальную версию MetaCleaner — временные файлы должны иметь расширение оригинала.

### Удалить оставшиеся временные файлы

```bash
find /path/to/folder -name "*.metacleaner.tmp*" -delete
```

### CI: workflow не запускается

- Workflow должен быть в **default branch** (main) — закоммитьте и смержите
- PR должен содержать **изменение медиафайла** (jpg, png, mp4 и т.д.)
- Автор PR — **не** `github-actions[bot]`

### CI: `missing required tools`

Перезапустите job после push в MetaCleaner `main`. Убедитесь, что caller ссылается на `@main` (или актуальный тег).

---

## Структура репозитория

```
MetaCleaner/
├── metacleaner.sh                     # точка входа CLI
├── metacleaner/                       # Python-модули
│   ├── __main__.py                    # CLI, аргументы, параллельная обработка
│   ├── config.py                      # загрузка YAML-конфига + дефолты
│   ├── walker.py                      # рекурсивный обход + exclude-логика
│   ├── excludes.py                    # app icon detection + glob matching
│   ├── deps.py                        # проверка внешних зависимостей
│   ├── report.py                      # отчёт (text / JSON)
│   └── handlers/
│       ├── image.py                   # JPEG, PNG, WebP, HEIC
│       ├── svg.py                     # SVG (svgo)
│       ├── video.py                   # MP4, MOV, M4V, WebM, MKV
│       └── utils.py                   # общие утилиты (subprocess, temp files)
├── .github/workflows/
│   └── optimize-media.yml             # reusable workflow (CI-логика)
├── templates/
│   ├── caller-workflow.yml            # шаблон workflow для проектов
│   └── metacleaner-gitignore          # строки для .gitignore проектов
├── scripts/
│   └── install-org-workflow.sh        # раскатка по всей организации
├── metacleaner.yaml.example           # полный пример конфига
├── requirements.txt                   # Python-зависимости
└── README.md
```
