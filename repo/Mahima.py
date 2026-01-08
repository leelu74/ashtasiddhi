#!/usr/bin/env python3
"""
Mahima.py - Backend Operations Agent
Handles Docker, API endpoints, repository management, and system operations
"""

import os
import logging
import subprocess
import uvicorn
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import asyncio
import tempfile

# Import other agents
from Anima import AnimaAgent
from Isitva import IsitvaAgent
from Prapti import PraptiAgent

class AnalysisRequest(BaseModel):
    pdf_path: str
    options: Optional[Dict[str, Any]] = {}

class SearchRequest(BaseModel):
    keywords: List[str]
    max_papers: int = 10

class SimulationRequest(BaseModel):
    planet_params: Dict[str, Any]

class MahimaAgent:
    """Agent for backend operations and API management"""
    
    def __init__(self, data_dir: str = "/data"):
        self.logger = logging.getLogger("Mahima")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize other agents
        self.anima = AnimaAgent(data_dir)
        self.isitva = IsitvaAgent(data_dir)
        self.prapti = PraptiAgent()
        
        # FastAPI app
        self.app = FastAPI(
            title="Exoplanet Analysis API",
            description="API for multi-agent exoplanet analysis system",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {"message": "Exoplanet Analysis API", "version": "1.0.0"}
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "data_dir": str(self.data_dir),
                "database_exists": (self.data_dir / "exoplanets.db").exists()
            }
        
        @self.app.post("/analyze")
        async def analyze_pdf(request: AnalysisRequest):
            """Analyze a PDF file"""
            try:
                if not Path(request.pdf_path).exists():
                    raise HTTPException(status_code=404, detail="PDF file not found")
                
                results = self.anima.analyze_pdf(request.pdf_path)
                return JSONResponse(content=results)
                
            except Exception as e:
                self.logger.error(f"Analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/upload-and-analyze")
        async def upload_and_analyze(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
            """Upload and analyze a PDF file"""
            try:
                # Save uploaded file
                temp_dir = self.data_dir / "temp"
                temp_dir.mkdir(exist_ok=True)
                
                file_path = temp_dir / file.filename
                
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                # Run analysis in background
                results = self.anima.analyze_pdf(str(file_path))
                
                return JSONResponse(content={
                    "filename": file.filename,
                    "status": "analyzed",
                    "results": results
                })
                
            except Exception as e:
                self.logger.error(f"Upload and analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/search-papers")
        async def search_papers(request: SearchRequest):
            """Search for papers"""
            try:
                papers = self.anima.search_papers(request.keywords, request.max_papers)
                return JSONResponse(content={"papers": papers})
                
            except Exception as e:
                self.logger.error(f"Paper search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/simulate")
        async def run_simulation(request: SimulationRequest):
            """Run transit simulation"""
            try:
                results = self.anima.run_simulation(request.planet_params)
                return JSONResponse(content=results)
                
            except Exception as e:
                self.logger.error(f"Simulation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/summary")
        async def get_summary():
            """Get analysis summary"""
            try:
                summary = self.anima.get_analysis_summary()
                return JSONResponse(content=summary)
                
            except Exception as e:
                self.logger.error(f"Summary failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/exoplanets")
        async def get_exoplanets(
            habitable_only: bool = False,
            has_atmosphere: bool = False,
            detection_method: Optional[str] = None,
            min_radius: float = 0.1,
            max_radius: float = 20.0
        ):
            """Get filtered exoplanets data"""
            try:
                filters = {
                    'habitable_only': habitable_only,
                    'has_atmosphere': has_atmosphere,
                    'min_radius': min_radius,
                    'max_radius': max_radius
                }
                
                if detection_method:
                    filters['detection_method'] = detection_method
                
                data = self.isitva.search_exoplanets(filters)
                return JSONResponse(content={"exoplanets": data})
                
            except Exception as e:
                self.logger.error(f"Exoplanets query failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/statistics")
        async def get_statistics():
            """Get system statistics"""
            try:
                stats = self.isitva.get_statistics()
                return JSONResponse(content=stats)
                
            except Exception as e:
                self.logger.error(f"Statistics failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/setup-repos")
        async def setup_repositories():
            """Setup external repositories"""
            try:
                results = self.prapti.setup_repositories()
                return JSONResponse(content={"setup_results": results})
                
            except Exception as e:
                self.logger.error(f"Repository setup failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/export/{format_type}")
        async def export_data(format_type: str):
            """Export data in specified format"""
            try:
                if format_type not in ['json', 'csv', 'excel']:
                    raise HTTPException(status_code=400, detail="Invalid format type")
                
                file_path = self.isitva.export_data(format_type)
                
                return FileResponse(
                    path=file_path,
                    filename=Path(file_path).name,
                    media_type='application/octet-stream'
                )
                
            except Exception as e:
                self.logger.error(f"Export failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/backup")
        async def backup_database():
            """Create database backup"""
            try:
                backup_path = self.isitva.backup_database()
                return JSONResponse(content={
                    "status": "success",
                    "backup_path": backup_path
                })
                
            except Exception as e:
                self.logger.error(f"Backup failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/clear-data")
        async def clear_all_data():
            """Clear all data (use with caution!)"""
            try:
                self.isitva.clear_all_data()
                return JSONResponse(content={"status": "All data cleared"})
                
            except Exception as e:
                self.logger.error(f"Data clearing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def start_api(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the FastAPI server"""
        self.logger.info(f"Starting API server on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
    
    def generate_docker_files(self) -> Dict[str, str]:
        """Generate Docker configuration files"""
        docker_files = {}
        
        # Dockerfile
        dockerfile_content = '''FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    wget \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Expose ports
EXPOSE 8000 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV DATA_DIR=/data

# Default command (can be overridden)
CMD ["python", "Anima.py", "--api"]
'''
        
        docker_files['Dockerfile'] = dockerfile_content
        
        # docker-compose.yml
        compose_content = '''version: '3.8'

services:
  exoplanet-analysis:
    build: .
    ports:
      - "8000:8000"  # API
      - "8501:8501"  # Streamlit UI
    volumes:
      - ./data:/data
      - ./pdfs:/app/pdfs:ro  # Mount PDFs read-only
    environment:
      - DATA_DIR=/data
      - PYTHONPATH=/app
    command: python Anima.py --api
    
  exoplanet-ui:
    build: .
    ports:
      - "8502:8501"
    volumes:
      - ./data:/data
    environment:
      - DATA_DIR=/data
      - PYTHONPATH=/app
    command: streamlit run Vasitva.py --server.address=0.0.0.0 --server.port=8501
    depends_on:
      - exoplanet-analysis

volumes:
  data:
'''
        
        docker_files['docker-compose.yml'] = compose_content
        
        # .dockerignore
        dockerignore_content = '''__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.git
.gitignore
README.md
.DS_Store
.vscode
*.log
.pytest_cache
.coverage
htmlcov/
'''
        
        docker_files['.dockerignore'] = dockerignore_content
        
        return docker_files
    
    def write_docker_files(self, output_dir: Optional[str] = None) -> List[str]:
        """Write Docker files to disk"""
        if output_dir is None:
            output_dir = self.data_dir.parent
        
        output_path = Path(output_dir)
        docker_files = self.generate_docker_files()
        written_files = []
        
        for filename, content in docker_files.items():
            file_path = output_path / filename
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            written_files.append(str(file_path))
            self.logger.info(f"Written Docker file: {file_path}")
        
        return written_files
    
    def build_docker_image(self, tag: str = "exoplanet-analysis:latest") -> bool:
        """Build Docker image"""
        try:
            self.logger.info(f"Building Docker image: {tag}")
            
            result = subprocess.run(
                ["docker", "build", "-t", tag, "."],
                cwd=self.data_dir.parent,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("Docker image built successfully")
                return True
            else:
                self.logger.error(f"Docker build failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Docker build error: {e}")
            return False
    
    def run_docker_container(self, tag: str = "exoplanet-analysis:latest", 
                           detached: bool = True) -> bool:
        """Run Docker container"""
        try:
            cmd = ["docker", "run"]
            
            if detached:
                cmd.append("-d")
            
            cmd.extend([
                "-p", "8000:8000",
                "-p", "8501:8501",
                "-v", f"{self.data_dir}:/data",
                tag
            ])
            
            self.logger.info(f"Running Docker container: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Container started: {result.stdout.strip()}")
                return True
            else:
                self.logger.error(f"Container start failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Docker run error: {e}")
            return False
    
    def check_system_requirements(self) -> Dict[str, Any]:
        """Check system requirements and dependencies"""
        requirements = {
            'python_version': None,
            'docker_available': False,
            'git_available': False,
            'disk_space': None,
            'memory': None,
            'dependencies': {}
        }
        
        # Python version
        import sys
        requirements['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Docker
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            requirements['docker_available'] = result.returncode == 0
        except:
            requirements['docker_available'] = False
        
        # Git
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            requirements['git_available'] = result.returncode == 0
        except:
            requirements['git_available'] = False
        
        # Check Python dependencies
        required_packages = [
            'streamlit', 'fastapi', 'uvicorn', 'pandas', 'numpy',
            'matplotlib', 'plotly', 'PyPDF2', 'nltk', 'spacy',
            'requests', 'gitpython', 'sqlite3'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                requirements['dependencies'][package] = True
            except ImportError:
                requirements['dependencies'][package] = False
        
        return requirements
    
    def install_dependencies(self) -> bool:
        """Install missing dependencies"""
        try:
            requirements_file = self.data_dir.parent / "requirements.txt"
            
            if requirements_file.exists():
                result = subprocess.run(
                    ["pip", "install", "-r", str(requirements_file)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.logger.info("Dependencies installed successfully")
                    return True
                else:
                    self.logger.error(f"Dependency installation failed: {result.stderr}")
                    return False
            else:
                self.logger.error("requirements.txt not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Dependency installation error: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'timestamp': self.isitva.get_timestamp(),
            'data_directory': str(self.data_dir),
            'database_path': str(self.data_dir / "exoplanets.db"),
            'requirements': self.check_system_requirements(),
            'analysis_summary': self.anima.get_analysis_summary(),
            'disk_usage': {}
        }
        
        # Disk usage
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.data_dir)
            status['disk_usage'] = {
                'total_gb': total / (1024**3),
                'used_gb': used / (1024**3),
                'free_gb': free / (1024**3)
            }
        except:
            pass
        
        return status

def main():
    """Main entry point for Mahima agent"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Mahima - Backend Operations Agent")
    parser.add_argument("--api", action="store_true", help="Start API server")
    parser.add_argument("--docker-build", action="store_true", help="Build Docker image")
    parser.add_argument("--docker-run", action="store_true", help="Run Docker container")
    parser.add_argument("--docker-setup", action="store_true", help="Generate Docker files")
    parser.add_argument("--check-requirements", action="store_true", help="Check system requirements")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    
    args = parser.parse_args()
    
    agent = MahimaAgent()
    
    try:
        if args.api:
            agent.start_api(args.host, args.port)
        
        elif args.docker_build:
            success = agent.build_docker_image()
            print(f"Docker build: {'Success' if success else 'Failed'}")
        
        elif args.docker_run:
            success = agent.run_docker_container()
            print(f"Docker run: {'Success' if success else 'Failed'}")
        
        elif args.docker_setup:
            files = agent.write_docker_files()
            print(f"Docker files created: {files}")
        
        elif args.check_requirements:
            reqs = agent.check_system_requirements()
            import json
            print(json.dumps(reqs, indent=2))
        
        elif args.install_deps:
            success = agent.install_dependencies()
            print(f"Dependencies installation: {'Success' if success else 'Failed'}")
        
        elif args.status:
            status = agent.get_system_status()
            import json
            print(json.dumps(status, indent=2, default=str))
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()