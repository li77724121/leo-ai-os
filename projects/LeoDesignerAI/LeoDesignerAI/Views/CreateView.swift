import SwiftUI

struct CreateView: View {
    @State private var prompt = ""
    @State private var generatedImageURL: String?
    @State private var isLoading = false
    @State private var showCamera = false
    @State private var showPhotoPicker = false
    @State private var selectedImage: UIImage?
    @State private var showCutoutResult = false
    @State private var cutoutImage: UIImage?
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // AI生成区域
                    VStack(alignment: .leading, spacing: 12) {
                        Label("AI生成图片", systemImage: "sparkles")
                            .font(.headline)
                        
                        HStack {
                            TextField("描述你想生成的图片...", text: $prompt)
                                .textFieldStyle(.roundedBorder)
                            
                            Button(action: generateImage) {
                                if isLoading {
                                    ProgressView()
                                        .progressViewStyle(.circular)
                                } else {
                                    Image(systemName: "wand.and.stars")
                                }
                            }
                            .disabled(prompt.isEmpty || isLoading)
                            .buttonStyle(.borderedProminent)
                        }
                        
                        if let url = generatedImageURL, let imageURL = URL(string: url) {
                            AsyncImage(url: imageURL) { phase in
                                switch phase {
                                case .success(let img):
                                    img
                                        .resizable()
                                        .scaledToFit()
                                        .clipShape(RoundedRectangle(cornerRadius: 12))
                                case .failure:
                                    Image(systemName: "photo.badge.exclamationmark")
                                        .font(.largeTitle)
                                case .empty:
                                    ProgressView()
                                @unknown default:
                                    EmptyView()
                                }
                            }
                            .frame(height: 300)
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    
                    // 上传/抠图区域
                    VStack(alignment: .leading, spacing: 12) {
                        Label("AI抠图/换背景", systemImage: "scissors")
                            .font(.headline)
                        
                        HStack(spacing: 16) {
                            Button(action: { showCamera = true }) {
                                VStack {
                                    Image(systemName: "camera")
                                        .font(.title2)
                                    Text("拍照")
                                        .font(.caption)
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue.opacity(0.1))
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                            
                            Button(action: { showPhotoPicker = true }) {
                                VStack {
                                    Image(systemName: "photo.on.rectangle")
                                        .font(.title2)
                                    Text("选图")
                                        .font(.caption)
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.green.opacity(0.1))
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                        }
                        
                        if let img = selectedImage {
                            Image(uiImage: img)
                                .resizable()
                                .scaledToFit()
                                .frame(height: 200)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                            
                            Button("AI一键抠图") {
                                Task { await removeBackground() }
                            }
                            .buttonStyle(.borderedProminent)
                            .disabled(isLoading)
                        }
                        
                        if let cutout = cutoutImage {
                            HStack {
                                Text("✅ 抠图完成")
                                    .foregroundColor(.green)
                                Spacer()
                                Button("保存") { saveImage(cutout) }
                                    .buttonStyle(.bordered)
                            }
                            
                            Image(uiImage: cutout)
                                .resizable()
                                .scaledToFit()
                                .frame(height: 200)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                }
                .padding()
            }
            .navigationTitle("AI创作")
            .sheet(isPresented: $showCamera) {
                ImagePicker(sourceType: .camera, image: $selectedImage)
            }
            .sheet(isPresented: $showPhotoPicker) {
                ImagePicker(sourceType: .photoLibrary, image: $selectedImage)
            }
        }
    }
    
    private func generateImage() {
        isLoading = true
        Task {
            let url = await AIService.generate(prompt)
            await MainActor.run {
                generatedImageURL = url
                isLoading = false
            }
        }
    }
    
    private func removeBackground() async {
        guard let image = selectedImage else { return }
        isLoading = true
        let result = await AIService.removeBackground(image)
        await MainActor.run {
            cutoutImage = result
            isLoading = false
        }
    }
    
    private func saveImage(_ image: UIImage) {
        UIImageWriteToSavedPhotosAlbum(image, nil, nil, nil)
    }
}

#Preview {
    CreateView()
}
