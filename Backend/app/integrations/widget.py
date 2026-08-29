from __future__ import annotations

import uuid
from typing import Any


class WidgetService:
    """Service for generating embed code for merchant websites"""
    
    def __init__(self, merchant_id: uuid.UUID, api_base_url: str):
        self.merchant_id = merchant_id
        self.api_base_url = api_base_url.rstrip("/")
    
    def generate_embed_code(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generate embed code for merchant website"""
        widget_config = config or self._get_default_config()
        
        # Use public endpoint for embedded widgets
        script_url = f"{self.api_base_url}/api/v1/integrations/widget/public/{self.merchant_id}"
        
        embed_code = {
            "script_url": script_url,
            "merchant_id": str(self.merchant_id),
            "config": widget_config,
            "html_snippet": self._generate_html_snippet(widget_config, script_url),
            "react_snippet": self._generate_react_snippet(widget_config, script_url),
            "vue_snippet": self._generate_vue_snippet(widget_config, script_url),
        }
        
        return embed_code
    
    def _get_default_config(self) -> dict[str, Any]:
        """Get default widget configuration"""
        return {
            "position": "bottom-right",
            "theme": "light",
            "primary_color": "#6366f1",
            "welcome_message": "Hi! I'm Sarthi, your AI shopping assistant. How can I help you today?",
            "enable_recommendations": True,
            "enable_cart_sync": True,
            "auto_open": False,
            "mobile_position": "bottom-right"
        }
    
    def _generate_html_snippet(self, config: dict[str, Any], script_url: str) -> str:
        """Generate HTML embed snippet"""
        return f'''<!-- Sarthi AI Widget -->
<script>
  window.SarthiConfig = {self._serialize_config(config)};
</script>
<script src="{script_url}" async defer></script>
<!-- End Sarthi AI Widget -->'''
    
    def _generate_react_snippet(self, config: dict[str, Any], script_url: str) -> str:
        """Generate React component snippet"""
        return f'''// Sarthi AI Widget for React
import {{ SarthiWidget }} from '@sarthi-ai/react-widget';

function App() {{
  return (
    <SarthiWidget
      merchantId="{str(self.merchant_id)}"
      apiUrl="{self.api_base_url}"
      config={self._serialize_config(config)}
    />
  );
}}'''
    
    def _generate_vue_snippet(self, config: dict[str, Any], script_url: str) -> str:
        """Generate Vue component snippet"""
        return f'''<!-- Sarthi AI Widget for Vue -->
<template>
  <SarthiWidget
    :merchant-id="{str(self.merchant_id)}"
    :api-url="{self.api_base_url}"
    :config="sarthiConfig"
  />
</template>

<script>
import {{ SarthiWidget }} from '@sarthi-ai/vue-widget';

export default {{
  components: {{ SarthiWidget }},
  data() {{
    return {{
      sarthiConfig: {self._serialize_config(config)}
    }};
  }}
}};
</script>'''
    
    def _serialize_config(self, config: dict[str, Any]) -> str:
        """Serialize config to JSON string"""
        import json
        return json.dumps(config, indent=2)
    
    def generate_widget_js(self) -> str:
        """Generate the actual widget JavaScript file content"""
        # Build JavaScript without f-string to avoid template literal conflicts
        js_code = '''// Sarthi AI Widget - Auto-generated for merchant ''' + str(self.merchant_id) + '''
(function() {
  const MERCHANT_ID = "''' + str(self.merchant_id) + '''";
  const API_BASE = "''' + self.api_base_url + '''";
  
  class SarthiWidget {
    constructor() {
      this.config = window.SarthiConfig || {};
      this.container = null;
      this.isOpen = false;
      this.sessionId = this.generateSessionId();
    }
    
    generateSessionId() {
      return 'sess_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
      this.createContainer();
      this.createToggleButton();
      this.loadStyles();
      this.setupEventListeners();
    }
    
    createContainer() {
      this.container = document.createElement('div');
      this.container.id = 'sarthi-widget-container';
      this.container.style.cssText = this.getContainerStyles();
      document.body.appendChild(this.container);
    }
    
    getContainerStyles() {
      const position = this.config.position || 'bottom-right';
      const styles = {
        'bottom-right': 'position:fixed;bottom:80px;right:20px;width:350px;height:500px;z-index:9999;',
        'bottom-left': 'position:fixed;bottom:80px;left:20px;width:350px;height:500px;z-index:9999;',
        'top-right': 'position:fixed;top:20px;right:20px;width:350px;height:500px;z-index:9999;',
        'top-left': 'position:fixed;top:20px;left:20px;width:350px;height:500px;z-index:9999;'
      };
      return styles[position] + 'display:none;background:white;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.15);';
    }
    
    createToggleButton() {
      const button = document.createElement('button');
      button.id = 'sarthi-widget-toggle';
      button.innerHTML = '💬';
      button.style.cssText = this.getButtonStyles();
      button.onclick = () => this.toggle();
      document.body.appendChild(button);
    }
    
    getButtonStyles() {
      const position = this.config.position || 'bottom-right';
      const styles = {
        'bottom-right': 'position:fixed;bottom:20px;right:20px;',
        'bottom-left': 'position:fixed;bottom:20px;left:20px;',
        'top-right': 'position:fixed;top:20px;right:20px;',
        'top-left': 'position:fixed;top:20px;left:20px;'
      };
      const color = this.config.primary_color || '#6366f1';
      return styles[position] + 'width:56px;height:56px;border-radius:50%;border:none;background:' + color + ';color:white;font-size:24px;cursor:pointer;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.2);transition:transform 0.2s;';
    }
    
    toggle() {
      this.isOpen = !this.isOpen;
      this.container.style.display = this.isOpen ? 'block' : 'none';
    }
    
    loadStyles() {
      // Widget would load chat interface here
      this.container.innerHTML = `
        <div style="padding:20px;height:100%;display:flex;flex-direction:column;">
          <div style="font-weight:600;margin-bottom:10px;">Sarthi AI Assistant</div>
          <div id="sarthi-messages" style="flex:1;overflow-y:auto;border:1px solid #eee;padding:10px;border-radius:8px;margin-bottom:10px;">
            <div style="background:#f3f4f6;padding:8px;border-radius:8px;margin-bottom:8px;">${this.config.welcome_message || 'Hi! How can I help you today?'}</div>
          </div>
          <div style="display:flex;gap:8px;">
            <input type="text" id="sarthi-input" placeholder="Type your message..." style="flex:1;padding:8px;border:1px solid #ddd;border-radius:8px;">
            <button onclick="window.sarthiWidget.sendMessage()" style="padding:8px 16px;background:${this.config.primary_color || '#6366f1'};color:white;border:none;border-radius:8px;cursor:pointer;">Send</button>
          </div>
        </div>
      `;
    }
    
    setupEventListeners() {
      window.sarthiWidget = this;
    }
    
    async sendMessage() {
      const input = document.getElementById('sarthi-input');
      const message = input.value.trim();
      if (!message) return;
      
      const messagesDiv = document.getElementById('sarthi-messages');
      messagesDiv.innerHTML += `<div style="background:${this.config.primary_color || '#6366f1'};color:white;padding:8px;border-radius:8px;margin-bottom:8px;text-align:right;">${message}</div>`;
      input.value = '';
      
      try {
        const response = await fetch('${API_BASE}/api/v1/ai/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [{ role: 'user', content: message }],
            session_id: this.sessionId,
            context: { source: 'widget' }
          })
        });
        
        const data = await response.json();
        messagesDiv.innerHTML += `<div style="background:#f3f4f6;padding:8px;border-radius:8px;margin-bottom:8px;">${data.message}</div>`;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
      } catch (error) {
        messagesDiv.innerHTML += `<div style="background:#fee;padding:8px;border-radius:8px;margin-bottom:8px;">Sorry, I encountered an error. Please try again.</div>`;
      }
    }
  }
  
  // Initialize widget when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new SarthiWidget().init());
  } else {
    new SarthiWidget().init();
  }
})();
'''
        return js_code
    
    def generate_no_code_snippet(self, platform: str) -> str:
        """Generate no-code platform snippets (Shopify, Wix, etc.)"""
        snippets = {
            "shopify": f'''<!-- Add to theme.liquid before </body> -->
<div id="sarthi-widget-mount"></div>
<script>
  window.SarthiConfig = {{ merchantId: "{str(self.merchant_id)}" }};
</script>
<script src="{self.api_base_url}/widget/sarthi.js" async defer></script>''',
            
            "wix": f'''<!-- Add to Wix site using HTML iframe widget -->
<script>
  window.SarthiConfig = {{ merchantId: "{str(self.merchant_id)}" }};
</script>
<script src="{self.api_base_url}/widget/sarthi.js" async defer></script>''',
            
            "wordpress": f'''<!-- Add to WordPress using Custom HTML widget -->
<script>
  window.SarthiConfig = {{ merchantId: "{str(self.merchant_id)}" }};
</script>
<script src="{self.api_base_url}/widget/sarthi.js" async defer></script>'''
        }
        
        return snippets.get(platform, "Platform not supported")
