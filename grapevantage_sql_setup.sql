-- phpMyAdmin SQL Dump
-- version 4.9.3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Server version: 5.7.26
-- PHP Version: 7.4.2

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

DROP DATABASE IF EXISTS `grapevantage_rds`;
CREATE DATABASE IF NOT EXISTS `grapevantage_rds` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `grapevantage_rds`;

CREATE TABLE `bbw_product` (
  `shopify_product_id` varchar(200) PRIMARY KEY,
  `bbw_product_name` varchar(200) NOT NULL,
  `product_type` varchar(200),
  `product_description` longtext,
  `image` varchar(200),
  `shopify_sku` varchar(200),
  `price` float(5,2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `bbw_product_metafields` (
  `shopify_product_id` varchar(200) PRIMARY KEY,
  `acidity` varchar(200),
  `country` varchar(200),
  `dryness` varchar(200),
  `fermentation` varchar(200),
  `glass` varchar(200),
  `grape` varchar(200),
  `region` varchar(200),
  `tannin` varchar(200),
  `body` varchar(200),
  `varietals` longtext,
  FOREIGN KEY (`shopify_product_id`) REFERENCES bbw_product(`shopify_product_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `bbw_matched_orders` (
  `checkout_token` varchar(200),
  `order_datetime` timestamp(0),
  `product_name` varchar(200),
  `item_quantity` int(10) NOT NULL,
  `item_price` decimal(6,2) NOT NULL,
  `shopify_product_id` varchar(200),
  `product_type` varchar(200),
  PRIMARY KEY (`checkout_token`, `order_datetime`, `product_name`)
  -- FOREIGN KEY (`shopify_product_id`) REFERENCES bbw_product(`shopify_product_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `supplier` (
  `supplier_name` varchar(100) PRIMARY KEY,
  `supplier_type` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `matched_product_listing` (
  `bbw_product_name` varchar(100),
  `supplier_name` varchar(100),
  `supplier_original_product_name` varchar(100),
  `in_stock_status` boolean NOT NULL,
  `product_listing_old_price` decimal(10, 4) NOT NULL,
  `product_listing_current_price` decimal(10, 4) NOT NULL,
  PRIMARY KEY (`bbw_product_name`, `supplier_name`, `supplier_original_product_name`)
  -- FOREIGN KEY (`bbw_product_name`) REFERENCES bbw_product(`bbw_product_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  -- FOREIGN KEY (`supplier_name`) REFERENCES supplier(`supplier_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `unmatched_product_listing` (
  `supplier_original_product_name` varchar(200),
  `supplier_name` varchar(100),
  `in_stock_status` boolean NOT NULL,
  `product_listing_old_price` decimal(10, 4) NOT NULL,
  `product_listing_current_price` decimal(10, 4) NOT NULL,
  PRIMARY KEY (`supplier_original_product_name`, `supplier_name`)
  -- FOREIGN KEY (`supplier_name`) REFERENCES supplier(`supplier_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `scrape_logs` (
  `supplier_name` varchar(100),
  `scraped_data_datetime` datetime(0) NOT NULL,
  PRIMARY KEY (`supplier_name`, `scraped_data_datetime`)
  -- FOREIGN KEY (`supplier_name`) REFERENCES supplier(`supplier_name`) ON DELETE CASCADE ON UPDATE CASCADE
  -- FOREIGN KEY (`scraped_data_datetime`) REFERENCES scraped_data(`scraped_data_datetime`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

/* CREATE TABLE `historical_demand` (
  `product_name` varchar(200),
  `supplier_name` varchar(100),
  `historical_demand_date` date NOT NULL,
  `historical_demand_sales` int(10) NOT NULL,
  PRIMARY KEY (`product_name`, `supplier_name`, `historical_demand_date`)
  -- FOREIGN KEY (`product_name`) REFERENCES product(`product_name`) ON DELETE CASCADE ON UPDATE CASCADE,
  -- FOREIGN KEY (`supplier_name`) REFERENCES supplier(`supplier_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `predicted_demand` (
  `product_name` varchar(200),
  `predicted_demand_target_date` date NOT NULL,
  `predicted_demand_prediction` decimal(18, 4) NOT NULL,
  PRIMARY KEY (`product_name`, `predicted_demand_target_date`)
  -- FOREIGN KEY (`product_name`) REFERENCES product(`product_name`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8; */

CREATE TABLE `schedule_params` (
  `scheduler_id` int(11) NOT NULL AUTO_INCREMENT,
  `day` varchar(100) NOT NULL,
  PRIMARY KEY (`scheduler_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `webscrape_params` (
  `supplier_name` varchar(100) PRIMARY KEY,
  `website_url` varchar(200) NOT NULL,
  `category` varchar(200),
  `country` varchar(200),
  `region` varchar(200),
  `rating` varchar(200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `webscrape_params` (`supplier_name`, `website_url`, `category`, `country`, `region`, `rating`) VALUES
('wine.delivery', 'https://wine.delivery/Buy-Wine-Online', 'White Wine', 'Italy', '', ''),
('vivino', 'https://www.vivino.com/explore', 'Rosé, Sparkling', 'Chile, Argentina, Australia', '', ''),
('pivene', 'https://www.pivene.com/collections/all', '', '', '', ''),
('twdc', 'https://twdc.com.sg/product-search/', '', '', '', ''),
('winedelivery', 'https://winedelivery.sg/product-category/wine/', '', '', '', ''),
('winelistasia', 'https://www.winelistasia.com/online-shop.html', '', '', '', ''),
('winesonline', 'https://winesonline.com.sg/collections/wines', '', '', '', ''),
('wineswholesales', 'https://www.wineswholesales.com.sg/collections/all-products?page=1', '', '', '', '');


INSERT INTO `schedule_params` (`day`) VALUES
('13');

INSERT INTO `supplier` (`supplier_name`, `supplier_type`) VALUES
('wine.delivery', 'competitor'),
('vivino', 'competitor'),
('pivene', 'competitor'),
('twdc', 'competitor'),
('winedelivery', 'competitor'),
('winelistasia', 'competitor'),
('winesonline', 'competitor'),
('wineswholesales', 'competitor');