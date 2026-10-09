### Общая памятка на весь семинар. Основные команды гита:
    
-   `git --version` — проверить установку.
-   `git config --global user.name "..."` — настроить имя пользователя.
-   `git config --global user.email "..."` — настроить email.
-   `git init` — создать локальный репозиторий.
-   `git clone <url>` — скопировать репозиторий (например, с Гитхаба).
-   `git status` — проверить состояние файлов.
-   `git add .` / `git add <file>` — добавить изменения в индекс.
-   `git commit -m "..."` — сохранить изменения (коммит).
-   `git log` — посмотреть историю коммитов.
-   `git log --oneline` — краткая история коммитов.
-   `git diff` — посмотреть разницу между версиями.
-   `git branch` — список веток.
-   `git branch <name>` — создать ветку.
-   `git checkout <name>` — переключиться на ветку.
-   `git checkout -b <name>` — создать и сразу переключиться на ветку.
-   `git merge <name>` — слить ветку.
-   `git branch -d <name>` — удалить ветку.
-   `git checkout -- <file>` — отменить изменения в файле (до коммита).
-   `git restore <file>` — современный аналог отмены изменений.
-   `git reset HEAD~1` — отменить последний коммит, сохранив изменения.
-   `git revert <hash>` — безопасно отменить коммит новым коммитом.
-   `touch .gitignore` — создать файл игнорирования.
-   `git rm --cached <file>` — убрать файл из индекса, не удаляя с диска.
-   `git stash` — временно спрятать изменения.        

### Установка и настройка гита

- Установка на Linux:
    ```bash   
    sudo apt install git
    ```
    
	-   На Windows (для справки): Скачать с `https://git-scm.com/install/windows`.
    
-   Проверка версии:
    ```bash
    git --version
    ```    
-   Настройка пользователя (обязательно!):
    
    ```bash    
    git config --global user.name "Ivan Ivanov"
    git config --global user.email "ivan@example.com"
    ```
    
    *Объяснить: это нужно, чтобы Гит знал, кто сделал коммит, иначе он не даст его создать.*
    
Предлагается сделать вместе со студентами мини-проект «Текстовая игра».
### Создание репозитория и основные команды

1.  Создаем папку проекта и инициализируем Git:
    
    ```bash
    mkdir text-adventure
    cd text-adventure
    git init
    ```
        
2.  Создаем структуру проекта (эмуляция кода):
    
    ```bash
    echo "# Моя игра" > README.md
    mkdir scripts
    echo "Player HP: 100" > scripts/player.txt
    echo "Enemy HP: 50" > scripts/enemy.txt
    ```
3.  Проверяем статус:
    
    ```bash
    git status
    ```
    *Красные файлы — они не отслеживаются.*
    
4.  Добавляем файлы в индекс (Staging area):       
    ```bash
    git add README.md
    git add scripts/player.txt
    git add scripts/enemy.txt
    ```
    или же просто
    ```bash
    git add .
    ```
    *Снова `git status` — файлы стали зелеными.*
    
5.  Делаем первый коммит:
    
    ```bash
    git commit -m "Initial commit: added README and scripts"
    ```
6.  Вносим изменения и коммитим:
    ```bash
    echo "Player damage: 10" >> scripts/player.txt    
    git add scripts/player.txt    
    git commit -m "Added player damage stat"
    ```
7.  Смотрим историю:
    
    ```bash
    git log
    ```     

### Ветвление и слияние

-   **Зачем:** Чтобы экспериментировать, не ломая основную ветку (`main`/`master`).
    
-   Создаем ветку для новой фичи:
    
    ```bash
    git branch feature-combat
    git checkout feature-combat
    ```    
-   Работаем в ветке:
    ```bash
    echo "Enemy attack: 5" > scripts/enemy.txt
    git add scripts/enemy.txt    
    git commit -m "Added enemy attack logic"
    ```        
-   Возвращаемся в main:
    
    ```bash
    git checkout main
    ```
    *Обратить внимание: файл `enemy.txt` вернулся к старому состоянию! Это магия веток.*
    
-   Сливаем изменения:
    
    ```bash
    git merge feature-combat
    ```
    _Теперь изменения из ветки попали в main._
    
-   Удаляем ненужную ветку:
    
    ```bash
    git branch -d feature-combat
    ```

### Задание для самостоятельной работы

Работать в новой ветке `feature-magic`.
1. Создать папку `skills` и в ней файл `fireball.txt`
2. Записать в этот файл
	```text
	Damage: 10;
	Manacost: 15
	```
3. Сделать коммит и слить изменения с главной веткой.
4. Удалить ветку `feature-magic`.

Решение:
```bash
git checkout -b feature-magic
mkdir skills
echo "Damage: 10;\n" > skills/fireball.txt
echo "Manacost: 15" > skills/fireball.txt
git add skills/fireball.txt
git commit -m "Add fireball skill"
git checkout main
git merge feature-magic
git branch -d feature-magic
```

### Что такое .gitignore и как его писать

-   **Проблема:** В проекте есть файлы, которые не нужны в репозитории (логи, кэш, системный мусор, настройки IDE).
    
-   Демонстрация. Cоздадим мусор:
    
    ```bash
    mkdir logs
    echo "Error 404" > logs/debug.log
    mkdir build
    echo "Binary data" > build/game.exe
    ```
      *`git status` покажет эти файлы. Если мы их закоммитим, репозиторий распухнет.*
    
-   Создаем `.gitignore`:
    ```bash
    touch .gitignore
    vim .gitignore  (или любой другой редактор)
    ```
-   Пишем правила:
    
    ```text
    # Игнорируем папку с логами
    logs/
    # Игнорируем папку сборки
    build/
    # Игнорируем все файлы с расширением .log
    *.log
    # Игнорируем файлы ОС (например, macOS)
    .DS_Store
    ```
    
-   Проверяем:  `git status` — файлы `logs/debug.log` и `build/game.exe` исчезли из списка неотслеживаемых.
    
-   **Важно:** Сам файл `.gitignore` нужно закоммитить!
    
    ```bash
    git add .gitignore
    git commit -m "Added .gitignore"
    ```
    

### Спасение утопающих: Откат изменений
Данные ситуации тоже можно разобрать со студентами совместно, если останется время.

-   **Ситуация 1:** Я изменил файл, но понял, что это ошибка, и хочу вернуть как было (до коммита):
    
    ```bash
    git checkout -- scripts/player.txt
    ```
    *Файл вернется к состоянию последнего коммита.*
    
-   **Ситуация 2:** Я хочу отменить последний коммит, но сохранить изменения в файлах:
    
    ```bash
    git reset HEAD~1
    ```
-   **Ситуация 3:** Безопасный откат (рекомендуется для команд):
    
    ```bash
    git log  (находим хеш нужного коммита, например, a3f5c9e)
    git revert a3f5c9e
    ```
    
    *Git создаст новый коммит, который отменяет изменения старого. История не переписывается.*
    
-   **Опасный откат** (упомянуть, что не надо делать без нужды):
    
    ```bash
    git reset --hard <hash>
    ```
    *Удаляет все изменения после указанного коммита. Использовать с осторожностью!*
