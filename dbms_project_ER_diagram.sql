-- Users
CREATE TABLE Users (
  user_id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  role VARCHAR(20) DEFAULT 'user',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories
CREATE TABLE Categories (
  category_id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL
);

-- Lost items
CREATE TABLE Lost_Items (
  lost_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES Users(user_id),
  title VARCHAR(150),
  description TEXT,
  category_id INT REFERENCES Categories(category_id),
  color VARCHAR(50),
  brand VARCHAR(100),
  date_lost DATE,
  location VARCHAR(200),
  image_url TEXT,
  status VARCHAR(20) DEFAULT 'pending', -- pending/matched/returned
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Found items
CREATE TABLE Found_Items (
  found_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES Users(user_id),
  title VARCHAR(150),
  description TEXT,
  category_id INT REFERENCES Categories(category_id),
  color VARCHAR(50),
  brand VARCHAR(100),
  date_found DATE,
  location VARCHAR(200),
  image_url TEXT,
  status VARCHAR(20) DEFAULT 'available', -- available/claimed
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches
CREATE TABLE Matches (
  match_id SERIAL PRIMARY KEY,
  lost_id INT REFERENCES Lost_Items(lost_id) ON DELETE CASCADE,
  found_id INT REFERENCES Found_Items(found_id) ON DELETE CASCADE,
  similarity_score FLOAT,
  match_status VARCHAR(20) DEFAULT 'suggested', -- suggested/confirmed/rejected
  suggested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  confirmed_by INT REFERENCES Users(user_id)
);

-- Notifications
CREATE TABLE Notifications (
  notification_id SERIAL PRIMARY KEY,
  user_id INT REFERENCES Users(user_id),
  message TEXT,
  link TEXT,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_lost_category ON Lost_Items(category_id);
CREATE INDEX idx_found_category ON Found_Items(category_id);
CREATE INDEX idx_match_score ON Matches(similarity_score);