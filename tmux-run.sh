#!/bin/bash
# This script creates a tmux session to monitor process logs
# Started by Riley C on 04/02/2026

echo "To switch between windows use CTRL-B <WINDOW #>"
echo "To disconnect use CTRL-B d, NOT CTRL-D"
sleep 2
# ────────────────────────────────────────────────────────────────────────────────
# Start tmux session
# ────────────────────────────────────────────────────────────────────────────────

tmux new-session -d -s fadb

# Create windows
tmux new-window -d -n console     -t fadb:0 "bash"
tmux send -t fadb:0 "source venv/bin/activate" C-m
tmux send -t fadb:0 "streamlit run ./firearm-db.py" C-m
# Attach to the session
tmux attach -t fadb



