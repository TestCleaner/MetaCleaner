# MetaCleaner

Инструмент для **очистки метаданных** и **сжатия медиафайлов** в папках и проектах любого типа (Flutter, iOS, Android, веб, просто архив фото/видео).

MetaCleaner рекурсивно обходит указанную директорию, находит изображения, иконки и видео по расширению, удаляет лишние метаданные (EXIF, GPS, container tags) и сжимает файлы без заметной потери качества на экране телефона.

> **Важно:** файлы заменяются **на месте**, без создания бэкапов. Перед первым запуском используйте `--dry-run` или сделайте копию папки / закоммитьте изменения в git.

---

## Содержание

- [Что делает инструмент](#что-делает-инструмент)
- [Поддерживаемые форматы](#поддерживаемые-форматы)
- [Установка](#установка)
- [Быстрый старт](#быстрый-старт)
- [Команды и флаги](#команды-и-флаги)
- [Примеры использования](#примеры-использования)
- [Конфигурация](#конфигурация)
- [Как обрабатывается каждый формат](#как-обрабатывается-каждый-формат)
- [Поведение и безопасность](#поведение-и-безопасность)
- [Коды выхода](#коды-выхода)
- [Устранение проблем](#устранение-проблем)
- [GitHub Organization (автоматизация для всех проектов)](#github-organization-автоматизация-для-всех-проектов)

---

## Что делает инструмент

1. **Один проход** по папке — быстрый рекурсивный обход с пропуском служебных директорий (`node_modules`, `build`, `.git`, `Pods` и др.)
2. **Очистка метаданных** — EXIF, GPS, IPTC, XMP, теги контейнера видео
3. **Сжатие** — уменьшение размера файла при визуально приемлемом качестве (аналог TinyPNG для фото)
4. **Замена на месте** — оптимизированный файл сразу подменяет оригинал
5. **Защита от увеличения** — если результат не меньше оригинала, файл не трогается

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

Список расширений можно изменить в конфиге `.metacleaner.yaml`.

---

## Установка

### Требования

- **Python 3.10+**
- Внешние утилиты (устанавливаются один раз в систему)

### macOS (Homebrew)

```bash
brew install exiftool ffmpeg mozjpeg pngquant webp svgo oxipng

git clone <repo-url> MetaCleaner
cd MetaCleaner
python3 -m pip install -r requirements.txt
chmod +x metacleaner.sh
```

### Linux (Debian/Ubuntu)

```bash
sudo apt install libimage-exiftool-perl ffmpeg mozjpeg pngquant webp svgo oxipng

cd MetaCleaner
python3 -m pip install -r requirements.txt
chmod +x metacleaner.sh
```

### Проверка зависимостей

```bash
./metacleaner.sh --doctor .
```

Покажет, какие утилиты установлены, а какие отсутствуют. Для обработки нужны только те инструменты, форматы которых реально есть в папке.

---

## Быстрый старт

```bash
# 1. Превью — ничего не меняет
./metacleaner.sh /path/to/folder --dry-run --verbose

# 2. Применить изменения
./metacleaner.sh /path/to/folder -j 8
```

Работает как с **проектом** (`/path/to/flutter_app`), так и с **обычной папкой медиа** (`~/Pictures/vacation`).

---

## Команды и флаги

```
./metacleaner.sh <путь> [опции]
```

| Флаг | Описание |
|------|----------|
| `<путь>` | Папка для обработки (обязательный аргумент) |
| `--dry-run` | Показать, что будет обработано, без изменений |
| `--verbose` | Выводить статус каждого файла |
| `-j`, `--jobs N` | Параллельных потоков (по умолчанию: 4) |
| `--images-only` | Только изображения и SVG |
| `--videos-only` | Только видео |
| `--config FILE` | Путь к YAML-конфигу |
| `--json` | Отчёт в формате JSON |
| `--check` | Exit code 1, если найдены медиафайлы (режим проверки) |
| `--doctor` | Проверить установленные зависимости |
| `--files FILE ...` | Обработать только указанные файлы |

### Альтернативный запуск (без shell-скрипта)

```bash
export PYTHONPATH=/path/to/MetaCleaner
python3 -m metacleaner /path/to/folder --dry-run
```

---

## Примеры использования

### Проект Flutter / iOS / Android

```bash
./metacleaner.sh ~/Projects/MyApp/assets --dry-run --verbose
./metacleaner.sh ~/Projects/MyApp/assets -j 8
```

### Папка с фото и видео (не проект)

```bash
./metacleaner.sh ~/Downloads/media --dry-run
./metacleaner.sh ~/Downloads/media
```

### Только картинки (без видео)

```bash
./metacleaner.sh /path/to/project --images-only -j 8
```

### Только видео

```bash
./metacleaner.sh /path/to/project --videos-only
```

### JSON-отчёт для скриптов

```bash
./metacleaner.sh /path/to/project --json > report.json
```

### Пример вывода

```
Project: /Users/me/MyApp/assets
Mode: apply
Scanned: 142
Optimized: 98
Skipped: 41
Failed: 3
Saved: 12.4 MB
```

- **Optimized** — файл сжат и заменён
- **Skipped** — оптимизированная версия не меньше оригинала
- **Failed** — ошибка обработки (см. список внизу отчёта)

---

## Конфигурация

Скопируйте пример в обрабатываемую папку или проект:

```bash
cp metacleaner.yaml.example /path/to/project/.metacleaner.yaml
```

MetaCleaner ищет конфиг в:
1. Путь из `--config`
2. `.metacleaner.yaml` в корне обрабатываемой папки
3. `metacleaner.yaml` в корне обрабатываемой папки

Если конфига нет — используются значения по умолчанию.

### Все параметры

```yaml
# Качество JPEG (MozJPEG)
jpeg_quality: 85

# PNG: диапазон качества pngquant ("мин-макс")
# Чем выше — меньше артефактов в градиентах, но больше файл
png_quality: "92-100"
png_speed: 1          # 1 = лучшее качество, 11 = быстрее
png_lossless: false   # true = oxipng без потерь (для идеальных градиентов)

# WebP
webp_quality: 80

# Видео H.264 (mp4, mov, m4v, mkv)
video_crf: 24         # 18–28: меньше = лучше качество
video_preset: fast    # ultrafast … veryslow

# WebM (VP9)
video_webm_cpu_used: 2  # 0 = лучше качество, 5 = быстрее

# Общие настройки
strip_metadata: true   # удалять метаданные
skip_if_larger: true   # не заменять, если файл стал больше
subprocess_timeout: 300

# Папки, которые полностью пропускаются при обходе
exclude_dirs:
  - .git
  - node_modules
  - build
  - Pods
  - DerivedData
  # ...

# Glob-паттерны для исключения отдельных файлов
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

### Настройка PNG при артефактах в градиентах

```yaml
png_quality: "95-100"   # поднять минимальное качество
png_speed: 1
```

Или полностью без потерь:

```yaml
png_lossless: true   # нужен oxipng: brew install oxipng
```

---

## Как обрабатывается каждый формат

| Формат | Инструмент | Действие |
|--------|------------|----------|
| JPEG | MozJPEG (`djpeg` → `cjpeg`) | Пересжатие + удаление EXIF |
| PNG | pngquant / oxipng | Сжатие с палитрой или lossless |
| WebP | cwebp | Сжатие + `-metadata none` |
| HEIC | FFmpeg | Конвертация в JPEG + strip metadata |
| SVG | svgo | Минификация + очистка editor metadata |
| MP4/MOV/M4V | FFmpeg libx264 | CRF-сжатие + strip metadata |
| MKV | FFmpeg libx264 | CRF-сжатие + strip metadata |
| WebM | FFmpeg libvpx-vp9 | VP9-сжатие + strip metadata |

---

## Поведение и безопасность

- Файлы **заменяются сразу** — бэкапы не создаются
- Рекомендуется перед первым запуском:
  - `./metacleaner.sh <путь> --dry-run --verbose`
  - или копия папки / git commit
- Если оптимизированный файл **больше или равен** оригиналу — оригинал сохраняется (`skip_if_larger: true`)
- HEIC конвертируется в `.jpg` — исходный `.heic` удаляется (учитывайте ссылки в проекте)
- Временные файлы (`*.metacleaner.tmp*`) создаются рядом с оригиналом и удаляются после обработки
- Служебные папки (`build`, `.git`, `node_modules`, `Pods` и др.) автоматически пропускаются

---

## Коды выхода

| Код | Значение |
|-----|----------|
| `0` | Успех |
| `1` | Есть ошибки обработки (`--doctor` — отсутствуют зависимости; `--check` — найдены медиафайлы) |
| `2` | Ошибка аргументов или путь не является папкой |

---

## Устранение проблем

### `missing required tools: pngquant`

Установите недостающую утилиту:

```bash
brew install pngquant   # macOS
./metacleaner.sh --doctor .
```

### Артефакты (полосы) в градиентах PNG

Поднимите `png_quality` до `"95-100"` или включите `png_lossless: true`.

### Ошибка WebM: `Only VP8 or VP9 or AV1...`

WebM не поддерживает H.264. MetaCleaner автоматически использует VP9 для `.webm` — убедитесь, что используете актуальную версию.

### Ошибка FFmpeg: `Unable to choose an output format`

Убедитесь, что используете актуальную версию — временные файлы должны иметь вид `file.metacleaner.tmp.mp4`, а не `file.mp4.metacleaner.tmp`.

### Удалить оставшиеся временные файлы

```bash
find /path/to/folder -name "*.metacleaner.tmp*" -delete
```

### Восстановить файлы после обработки

Встроенного restore нет. Варианты:
- `git checkout -- .` (если файлы в git)
- восстановить из Time Machine / облака / ручной копии

---

## GitHub Organization (автоматизация для всех проектов)

MetaCleaner можно подключить ко **всем репозиториям организации**. Разработчики ничего не устанавливают локально — при PR с медиафайлами GitHub Action автоматически добавляет отдельный коммит `chore: optimize media assets`.

### Как это работает

```
Разработчик: git push → открывает PR с photo.png
       ↓
GitHub Action (ubuntu-latest)
       ↓
MetaCleaner обрабатывает только изменённые медиа
       ↓
Коммит от github-actions[bot] в ту же ветку PR
```

### Шаг 1. Запушить MetaCleaner в org

Репозиторий `your-org/MetaCleaner` должен содержать reusable workflow:

```
.github/workflows/optimize-media.yml   ← общая логика (уже в этом репо)
```

### Шаг 2. Раскатать workflow по всем проектам org

```bash
# Установить gh: https://cli.github.com/
gh auth login

# Превью (без изменений)
./scripts/install-org-workflow.sh YOUR_ORG MetaCleaner --dry-run

# Создать PR в каждом репозитории org
./scripts/install-org-workflow.sh YOUR_ORG MetaCleaner
```

Скрипт в каждый проект (кроме MetaCleaner) добавляет `.github/workflows/optimize-media.yml` и открывает PR.

### Шаг 3. Вручную (один проект)

Скопируйте шаблон:

```bash
cp templates/caller-workflow.yml /path/to/project/.github/workflows/optimize-media.yml
```

Замените `@ORG@` и `@METACLEANER@` на вашу организацию и имя репо.

### Шаг 4. (Опционально) Конфиг в проектах

```bash
cp metacleaner.yaml.example /path/to/project/.metacleaner.yaml
# настройте exclude_dirs под структуру проекта
```

### Что видит разработчик

- Пушит код с новой картинкой / видео
- Через 1–10 минут в PR появляется коммит `chore: optimize media assets`
- Локально ничего ставить не нужно

### Ограничения

| Ситуация | Поведение |
|----------|-----------|
| PR из fork внешнего контributor | auto-commit **не работает** (ограничение GitHub) |
| PR внутри org | ✅ работает |
| Большие видео | job может идти долго; отключите видео: `process_videos: false` в caller workflow |
| Повторный push от bot | пропускается (`if: github.actor != 'github-actions[bot]'`) |

### Обновление логики для всех проектов

Изменения в `.github/workflows/optimize-media.yml` в репо MetaCleaner автоматически подхватываются всеми проектами (caller ссылается на `@main`).

Для фиксации версии замените `@main` на `@v1.0.0` в caller workflow.

---

## Структура репозитория

```
MetaCleaner/
├── metacleaner.sh
├── metacleaner/
├── .github/workflows/
│   └── optimize-media.yml      # reusable workflow для org
├── templates/
│   └── caller-workflow.yml     # шаблон для проектов
├── scripts/
│   └── install-org-workflow.sh # раскатка по org
├── metacleaner.yaml.example
├── requirements.txt
└── README.md
```
