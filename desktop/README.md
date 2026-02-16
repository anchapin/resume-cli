# ResumeAI Desktop

A desktop application for managing resumes and tracking job applications, built with Tauri and PWA technology.

## Features

- **Resume Management**: Edit and preview your resume.yaml with syntax highlighting
- **AI-Powered Generation**: Generate tailored resumes and cover letters using AI
- **Application Tracking**: Log and track job applications with status updates
- **Analytics Dashboard**: Visualize your application progress with charts
- **Offline Support**: Works offline using PWA service workers
- **Cross-Platform**: Runs on Windows, macOS, and Linux

## Technology Stack

- **Frontend**: Vanilla JavaScript, CSS3, HTML5
- **Desktop Wrapper**: Tauri v2 (Rust-based)
- **PWA**: Service Worker for offline capability
- **Storage**: IndexedDB + localStorage for local data persistence
- **API**: Integrates with Resume CLI REST API

## Installation

### Prerequisites

1. **Node.js** (v18 or higher)
2. **Rust** (for Tauri builds)
   - Install from: https://rustup.rs/
3. **Python 3** (for local development server)

### Development Setup

```bash
# Navigate to desktop directory
cd desktop

# Install Node dependencies
npm install

# Install Tauri CLI
npm install -g @tauri-apps/cli

# For development (runs in browser)
npm run serve

# For Tauri development (native window)
npm run dev

# Build for production
npm run build
```

### Platform-Specific Requirements

#### Windows
- WebView2 (usually pre-installed on Windows 10/11)
- Visual Studio C++ Build Tools

#### macOS
- Xcode Command Line Tools
- macOS 10.15 or later

#### Linux
- WebKit2GTK (for GTK-based systems)
- libwebkit2gtk-4.0-dev or libwebkit2gtk-4.1-dev
- libgtk-3-dev
- libayatana-appindicator3-dev

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

**Fedora:**
```bash
sudo dnf install -y \
    webkit2gtk3-devel \
    openssl-devel \
    gtk3-devel \
    libappindicator-gtk3-devel \
    librsvg2-devel
```

## Usage

### Running the Application

#### Development Mode (Browser)
```bash
cd desktop
python3 -m http.server 8080
# Open http://localhost:8080
```

#### Development Mode (Tauri)
```bash
cd desktop
npm run dev
```

#### Production Build
```bash
cd desktop
npm run build
# Binaries will be in desktop/src-tauri/target/release/bundle/
```

### First-Time Setup

1. **Load Resume Data**: Go to the Resume tab and load your `resume.yaml` file
2. **Configure API**: Go to Settings and enter your AI API keys (Anthropic or OpenAI)
3. **Start Tracking**: Add your first job application in the Tracking tab

### Keyboard Shortcuts

- `Ctrl/Cmd + R`: Refresh current view
- `Ctrl/Cmd + ,`: Open Settings
- `Escape`: Close modals

## Project Structure

```
desktop/
├── index.html              # Main HTML file
├── manifest.json           # PWA manifest
├── sw.js                   # Service worker
├── package.json            # Node.js configuration
├── src/
│   ├── css/
│   │   └── styles.css      # Main styles
│   └── js/
│       ├── api.js          # API client
│       ├── storage.js      # Local storage manager
│       ├── utils.js        # Utility functions
│       ├── app.js          # Main application
│       ├── components/
│       │   ├── toast.js    # Toast notifications
│       │   ├── modal.js    # Modal dialogs
│       │   └── charts.js   # Chart rendering
│       └── views/
│           ├── dashboard.js
│           ├── resume.js
│           ├── generate.js
│           ├── tracking.js
│           ├── analytics.js
│           └── settings.js
└── src-tauri/
    ├── Cargo.toml          # Rust dependencies
    ├── tauri.conf.json     # Tauri configuration
    ├── build.rs            # Build script
    └── src/
        └── main.rs         # Rust entry point
```

## API Integration

The desktop app integrates with the Resume CLI REST API. By default, it connects to `http://localhost:8000`.

### Starting the API Server

```bash
# From the project root
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Configuring API Connection

1. Go to Settings > AI API Configuration
2. Enter your API base URL (default: http://localhost:8000)
3. Enter your API key
4. Click "Test Connection"

## Offline Capability

The app uses a service worker to cache static assets and API responses:

- **Static Assets**: HTML, CSS, JS files are cached on first load
- **API Responses**: Successful API responses are cached for offline access
- **Local Data**: All application data is stored locally using IndexedDB

### Offline Limitations

- AI-powered features require an internet connection
- GitHub sync requires an internet connection
- PDF generation may require server access

## Data Storage

All data is stored locally:

- **Settings**: localStorage
- **Applications**: IndexedDB
- **Resume Content**: IndexedDB
- **Generated Files**: IndexedDB

### Export/Import Data

Go to Settings and use the Export/Import buttons to backup or restore your data.

## Building for Production

### Build Commands

```bash
# Build for current platform
npm run build

# Build specific target
tauri build --target <target-triple>
```

### Output Locations

- **Windows**: `src-tauri/target/release/bundle/msi/` and `nsis/`
- **macOS**: `src-tauri/target/release/bundle/dmg/` and `app/`
- **Linux**: `src-tauri/target/release/bundle/deb/` and `appimage/`

## Troubleshooting

### App Won't Start

1. Check that all dependencies are installed
2. Try running `npm run dev` to see error messages
3. Check the Tauri logs in the console

### API Connection Failed

1. Ensure the API server is running
2. Check the API URL in Settings
3. Verify your API key is correct

### Build Fails on Linux

Install missing dependencies:
```bash
sudo apt-get install -y libwebkit2gtk-4.0-dev libgtk-3-dev
```

### Service Worker Issues

Clear the service worker cache:
1. Open DevTools
2. Go to Application tab
3. Click "Unregister" next to the service worker
4. Reload the page

## Development

### Adding New Features

1. Create new view controller in `src/js/views/`
2. Add navigation item in `index.html`
3. Register in `app.js`
4. Add Tauri commands in `src-tauri/src/main.rs` if needed

### Testing

```bash
# Run tests (when implemented)
npm test

# Lint code
npm run lint
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Related Projects

- [Resume CLI](https://github.com/anchapin/ResumeAI) - The underlying CLI tool
- [Tauri](https://tauri.app/) - Desktop application framework
- [ResumeAI](https://github.com/anchapin/ResumeAI) - Main project repository
