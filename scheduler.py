import sqlite3

import threading

import time 

db_lock = threading.Lock()

def job_one():
    print("Job one starting....")
    time.sleep(3)
    print("Job one done!")

def job_two():
    print("Job two starting....")
    time.sleep(3)
    print("Job two done!")

conn = sqlite3.connect("jobs.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS jobs
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   job_name TEXT NOT NULL,
                   status TEXT NOT NULL)''')

conn.commit()

available_jobs = {
    "job_one" : job_one,
    "job_two" : job_two
}

def submit_job(job_name):        # parameter is named "job"
    cursor.execute(
        "INSERT INTO jobs (job_name, status) VALUES (?, ?)", 
        (job_name, 'pending')
    )
    conn.commit()
    print(f"Submitted: {job_name}")

def run_worker():
    cursor.execute("SELECT id, job_name FROM jobs WHERE status = 'pending'")
    pending_jobs = cursor.fetchall()

    threads = []
    for job_id, job_name in pending_jobs:
        job_function = available_jobs[job_name]
        t = threading.Thread(target=run_and_mark_done, args=(job_id, job_function))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

def run_and_mark_done(job_id, job_function):
    job_function()
    with db_lock:
        local_conn = sqlite3.connect("jobs.db")
        local_cursor = local_conn.cursor()
        local_cursor.execute("UPDATE jobs SET status = 'done' WHERE id = ?", (job_id,))
        local_conn.commit()
        local_conn.close()
    

submit_job("job_one")
submit_job("job_two")
run_worker()