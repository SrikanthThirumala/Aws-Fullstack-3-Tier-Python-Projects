mysql -h sri-rds.cvmq02608h73.us-west-2.rds.amazonaws.com -u admin -p'7y[Zl3uAk]tW~f]Wu?q38UMS~A:N'<test.sql


test.sql 
Create database testsridb;


curl -X GET "http://localhost:8000/items/"

Create database testsridb;


pm2 stop app.py --interpreter python3 --name 'flash-backend'

curl -X POST "http://localhost:8000/items/" \
     -H "Content-Type: application/json" \
     -d '{"name": "Admin User", "email": "admin@example.com", "country": "USA"}'

     curl -X GET "http://localhost:8000/items/"

CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL
);




mysql -h sri-rds-1.c3ome6gc6134.ap-south-1.rds.amazonaws.com -u admin -p'DOptpuP!kYtIb]:]4Mjr(eefp7E5'<test.sql

git pull origin main


     server {
    listen 80;
    server_name _;

    # 🔥  Proxy users endpoints directly
    location /api/ {
        set $backend "http://10.0.3.77:8000";
        rewrite ^/api/(.*)$ /$1 break;
        proxy_pass $backend;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;



    }

    # React / HTML frontend
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}


 server {
        listen       80;
        listen       [::]:80;
        server_name  _;
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

    location /api/ {
    # 1. Define the backend variable FIRST
    set $backend "http://10.0.3.77:8000";

    # 2. Strip /api from the URI path
    rewrite ^/api/(.*)$ /$1 break;

    # 3. Pass the rewritten request to the backend variable
    proxy_pass $backend;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
        error_page 404 /404.html;
        location = /404.html {
        }

        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
        }
    }







    Generate a  cloud architecture with the following 
I have vpc with cidr range 10.0.0.0/24 with 2 public subnets one in us-west2a and other in 2b  and 4 private subnets 2 private subnets have NAT attached one in 2a and other in 2b and on the first private subnet 2 private servers  created and are used for frontend and backend  each in different subnet but same 2a zone ,remaining 2 private subnets which are isolateed from internet are used for subnet grp for rds instance ,created a role for ec2 to assume role that includes ssm management instance core for using SSM to login private server from console and secret read/write for ec2 to fetch secrets of rds instance for logginfg into database from ec2 app.py, on backend server installed mysql client and created a testsridb with the table called items with fields id (auto incrment)name email country and after that created requirements.txt file with Flask,boto3,pymysql ,nodejs and installed python  pip ,to run requirements.txt and install depedencies and nodejs pm2 for running backend python file ,
On frontend server installed nginx to use it as web server ,deleted the content on index.html inside /usr/share/nginx/html/ and provided by updated homepage with the reverse proxy script configured ,proxy.conf file created in the same folder and provided rules for reverse proxy and also given the private hosted zone url for ip masking for reaching backend server & updated the path to config file in /etc/nginx/nginx.conf by #including created 2 target groups first tg for front end with target port as 80 for reaching front end server  and created front end alb with this target group ,another backend tartget group with target to 8000 where app.py runnign on backend private server and craeted LB for backend as well with this backend TG
created public facing hosted zone with custom domain pointing to http://srikanth-thirumala.int.yt/ with A record to frontend alb and private hosted zone with private-backend-api pointing to A record with backend alb that was craeted earlier 
meanwhile perfectly working frontend private  server with all the dependencies    custom image is created and also perfectly working backend private  server with all the files custom image also taken now with this first front end template is created with the custom ami and same config provided to earlier front end server and     attached role that was craeted earlier 
