import SwiftUI

struct SettingsView: View {
    @State private var openRouterKey = TranslationService.shared.openRouterKey
    @State private var deepseekKey = TranslationService.shared.deepseekKey
    @State private var ollamaURL = TranslationService.shared.ollamaURL
    @State private var saved = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("设置")
                .font(.title2)
                .fontWeight(.bold)

            GroupBox(label: Label("OpenRouter", systemImage: "network")) {
                VStack(alignment: .leading) {
                    SecureField("API Key", text: $openRouterKey)
                        .textFieldStyle(.roundedBorder)
                    HStack {
                        Text("免费额度: openrouter.ai/keys")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Spacer()
                        Button("获取") { NSWorkspace.shared.open(URL(string: "https://openrouter.ai/keys")!) }
                            .buttonStyle(.link)
                    }
                }
                .padding(4)
            }

            GroupBox(label: Label("DeepSeek", systemImage: "brain")) {
                VStack(alignment: .leading) {
                    SecureField("API Key", text: $deepseekKey)
                        .textFieldStyle(.roundedBorder)
                    Text("备用: platform.deepseek.com")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(4)
            }

            GroupBox(label: Label("Ollama (本地)", systemImage: "desktopcomputer")) {
                VStack(alignment: .leading) {
                    TextField("服务器地址", text: $ollamaURL)
                        .textFieldStyle(.roundedBorder)
                    Text("默认: http://localhost:11434 (Mac Mini)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(4)
            }

            HStack {
                if saved {
                    Text("✅ 已保存")
                        .foregroundColor(.green)
                        .font(.caption)
                }
                Spacer()
                Button("保存") {
                    TranslationService.shared.openRouterKey = openRouterKey
                    TranslationService.shared.deepseekKey = deepseekKey
                    TranslationService.shared.ollamaURL = ollamaURL
                    saved = true
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) { saved = false }
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding()
        .frame(width: 400, height: 360)
    }
}

#Preview {
    SettingsView()
}
