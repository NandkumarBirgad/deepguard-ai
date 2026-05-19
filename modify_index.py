import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_section = '''    <!-- Detector Cards Section -->
    <section id="upload-section" class="upload-section">
        <div class="container">
            <h2>Choose Your Detection Tool</h2>
            <div style="display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap; margin-top: 3rem;">
                
                <div class="card" style="flex: 1; min-width: 300px; text-align: center; cursor: pointer; transition: transform 0.3s;" onclick="window.location.href='/detect-ai'">
                    <i data-lucide="image" style="width: 64px; height: 64px; color: #8b5cf6; margin: 0 auto 1.5rem;"></i>
                    <h3 style="font-size: 1.75rem; margin-bottom: 1rem;">AI Image Detector</h3>
                    <p style="color: #94a3b8; margin-bottom: 2rem;">Detect AI-generated images and deepfakes using our advanced computer vision model.</p>
                    <button class="btn btn-primary" style="width: 100%;">Scan Image</button>
                </div>
                
                <div class="card" style="flex: 1; min-width: 300px; text-align: center; cursor: pointer; transition: transform 0.3s;" onclick="window.location.href='/detect-ai-video'">
                    <i data-lucide="video" style="width: 64px; height: 64px; color: #0ea5e9; margin: 0 auto 1.5rem;"></i>
                    <h3 style="font-size: 1.75rem; margin-bottom: 1rem;">AI Video Detector</h3>
                    <p style="color: #94a3b8; margin-bottom: 2rem;">Analyze videos frame-by-frame to identify synthetic content and face-swaps.</p>
                    <button class="btn btn-primary" style="width: 100%; background: linear-gradient(135deg, #0ea5e9, #3b82f6);">Scan Video</button>
                </div>
                
            </div>
        </div>
    </section>'''

html = re.sub(r'<section id="upload-section".*?</section>', new_section, html, flags=re.DOTALL)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
