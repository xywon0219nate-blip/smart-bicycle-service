# 데이터베이스 확인
show databases;

# pedalup_db 데이터베이스 생성
create database pedalup_db
	character set utf8mb4
    collate utf8mb4_unicode_ci;

# database 사용
use pedalup_db;

# 선택
select database();

# 테이블 리스트 조회 (처음엔 비어있음 - 서버 실행하면 user 테이블 자동 생성됨)
show tables;

# 서버 실행 후 회원가입 데이터 확인용
select * from member;