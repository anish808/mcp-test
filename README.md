# Spotify MCP Server

A Model Context Protocol (MCP) server that integrates with Spotify and provides AI-enhanced features. This project allows Claude to interact with your Spotify account to control playback, analyze music, and provide personalized recommendations.

## Features

- Get information about currently playing tracks
- Control playback (play, pause, next, previous)
- Get personalized music recommendations
- Analyze playlists for musical characteristics
- Create AI-generated playlists based on prompts
- View your top tracks and artists

## Architecture

The system is composed of multiple specialized MCP agents that work together:

### 1. Playback Control Agent
Handles real-time music playback operations:
- Play/pause/skip tracks
- Current playback status

### 2. Music Discovery Agent
Focuses on music recommendations and exploration:
- Song recommendations
- Mood-based suggestions

### 3. Playlist Management Agent
Manages playlist-related operations:
- Create/modify playlists
- Playlist analysis
- AI-generated playlists

### 4. User Insights Agent
Analyzes user's music preferences and history:
- Top tracks/artists
- Listening patterns

### 5. Audio Analysis Agent
Handles detailed music analysis:
- Track audio features
- Mood detection
- BPM/key analysis

## Setup

1. Create a `.env` file with your API credentials:

