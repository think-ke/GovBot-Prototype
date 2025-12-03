#!/bin/bash
set -e

# Step 3: Clear All Data
echo "WARNING: This will clear all data directories!"
echo "Make sure you have completed backups first."
echo ""
read -p "Type 'YES' to proceed: " confirmation

if [ "$confirmation" != "YES" ]; then
    echo "Aborting."
    exit 1
fi

echo "Stopping Docker services..."
docker compose down

echo "Clearing data directories..."
sudo rm -rf ./data/postgres/*
sudo rm -rf ./data/chroma/*
sudo rm -rf ./data/minio/*
sudo rm -rf ./data/metabase/*
sudo rm -rf ./data/backups/*
sudo rm -rf ./storage/*

echo "✓ All data cleared"
echo ""
echo "To start fresh:"
echo "  docker compose up -d --build"
