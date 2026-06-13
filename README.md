# 🚀 Project Description

## This project is a Telegram Bot for the Jahongir Academy platform.
### The bot allows users to take tests, receive certificates, and interact with academy channels.

## 🧰 Requirements

Before starting, make sure you have installed:

Python 3.10+

pip (Python package manager)

Redis (for caching and session storage)

PostgreSQL (as the main database)

## 📦 Installation

Clone the repository:

```shell
git clone https://github.com/username/project-name.git
cd project-name
```

Create a virtual environment:

``` shell
python -m venv venv
source venv/bin/activate      # for Linux/Mac
venv\Scripts\activate         # for Windows
```

Install dependencies:

``` shell
pip install -r requirements.txt
```

⚙️ Environment Setup

Copy the environment example file:
```shell
cp .env.dist .env
```

Open the .env file and fill in your own values:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=database_name
DB_USER=db_user
DB_PASSWORD=db_password

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password
REDIS_USER=redis_user
REDIS_USER_PASSWORD=redis_user_password

BASE_URL=https://jahongiracademy.uz
BOT_TOKEN=123456789:bot_token
ADMIN_ID=123456789

CERTIFICATE_ID=certificate_file_id1,certificate_file_id2,certificate_file_id3
CHANNELS_ID=JahongirAcademy
```

📁 Example .env.dist
```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=
REDIS_USER=
REDIS_USER_PASSWORD=

BASE_URL=https://jahongiracademy.uz
BOT_TOKEN=123456789:bot_token
ADMIN_ID=

CERTIFICATE_ID=certificate_file_id1,certificate_file_id2,certificate_file_id3,certificate_file_idn
CHANNELS_ID=channel_name
```

▶️ Running the Bot

After configuring your .env, start the bot using:

```
uvicorn main:app --reload
```
