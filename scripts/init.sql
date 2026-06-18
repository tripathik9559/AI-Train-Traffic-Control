-- Railway Control System — MySQL Initialization
-- Tables are created automatically by Django migrations.
-- This file only creates the database and user.

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS railway_control_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE railway_control_db;

SET FOREIGN_KEY_CHECKS = 1;