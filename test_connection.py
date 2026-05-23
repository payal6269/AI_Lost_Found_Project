import psycopg2
from urllib.parse import quote_plus

password = quote_plus('payal6269Nika@10965')
project = 'tdapvcfpihkskolkiiyy'

urls = [
    # Session pooler port 5432
    f'postgresql://postgres.{project}:{password}@aws-0-ap-south-1.pooler.supabase.com:5432/postgres',
    # Transaction pooler port 6543
    f'postgresql://postgres.{project}:{password}@aws-0-ap-south-1.pooler.supabase.com:6543/postgres',
    # Direct connection (no pooler)
    f'postgresql://postgres:{password}@db.{project}.supabase.co:5432/postgres',
    # Other regions session pooler
    f'postgresql://postgres.{project}:{password}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres',
    f'postgresql://postgres.{project}:{password}@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres',
]

for url in urls:
    display = url.split('@')[1]  # show only host:port part
    try:
        conn = psycopg2.connect(url, connect_timeout=8)
        conn.close()
        print(f'SUCCESS: {display}')
        print(f'FULL URL: {url}')
        break
    except Exception as e:
        print(f'FAILED:  {display} -> {str(e)[:80]}')
