# משתמשים באימג' הרשמי של AWS Lambda (במקום slim)
FROM public.ecr.aws/lambda/python:3.9

# העתקת קבצי הדרישות
COPY req.txt ${LAMBDA_TASK_ROOT}

# התקנת החבילות (כולל mangum שחייב להיות ב-requirements.txt)
RUN pip install -r req.txt

# העתקת שאר הקוד לתיקייה המיוחדת של למבדה
COPY . ${LAMBDA_TASK_ROOT}

# הגדרת הפקודה - הפעם למבדה תבין בדיוק מה זה אומר
CMD [ "main.handler" ]
