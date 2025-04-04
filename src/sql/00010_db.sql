if not exists (select name from sys.databases where name = N'Unidash')
    create database [Unidash];
