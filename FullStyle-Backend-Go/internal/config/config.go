package config

import (
	"encoding/json"
	"log"
	"os"
)

type Config struct {
	Port     string `json:"port"`
	Database string `json:"database"`
}

func LoadConfig() (*Config, error) {
	file, err := os.Open("config.json")
	if err != nil {
		log.Fatalf("Error opening config file: %v", err)
		return nil, err
	}
	defer file.Close()

	var config Config
	if err := json.NewDecoder(file).Decode(&config); err != nil {
		log.Fatalf("Error decoding config file: %v", err)
		return nil, err
	}

	return &config, nil
}
