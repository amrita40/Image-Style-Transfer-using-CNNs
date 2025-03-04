import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# Function to load and preprocess images
def load_image(image_path, max_size=400, shape=None):
    image = Image.open(image_path).convert("RGB")  # Removed grayscale conversion

    # Resize the image properly
    if shape is not None:
        shape = (int(shape[0]), int(shape[1]))  # Convert to tuple of integers
    else:
        size = max_size if max(image.size) > max_size else max(image.size)
        shape = (size, size)

    transform = transforms.Compose([
        transforms.Resize(shape),
        transforms.ToTensor()
    ])

    image = transform(image)[:3, :, :].unsqueeze(0)
    return image

# Load pre-trained VGG19 model
def get_vgg19():
    model = models.vgg19(pretrained=True).features  # Load pretrained model correctly
    for param in model.parameters():
        param.requires_grad_(False)  # Freeze parameters
    return model

# Extract features from VGG19
def get_features(image, model):
    layers = {
        'conv1_1': 0,  
        'conv2_1': 5,  
        'conv3_1': 10,  
        'conv4_1': 19,  
        'conv4_2': 21,  # Needed for content loss
        'conv5_1': 28,  
    }
    
    features = {}
    x = image
    for name, layer in enumerate(model):  
        x = layer(x)
        if name in layers.values():
            key = list(layers.keys())[list(layers.values()).index(name)]
            features[key] = x
    return features

# Compute Gram matrix for style representation
def gram_matrix(tensor):
    _, d, h, w = tensor.size()
    tensor = tensor.view(d, h * w)
    gram = torch.mm(tensor, tensor.t())
    return gram

# Function to apply style transfer
def style_transfer(content_path, style_path, output_path, steps=500, alpha=1, beta=1e7):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load images
    content = load_image(content_path).to(device)
    style = load_image(style_path, shape=content.shape[-2:]).to(device)  # Ensure both images have the same shape

    # Load VGG19 model
    vgg = get_vgg19().to(device).eval()

    # Extract features
    content_features = get_features(content, vgg)
    style_features = get_features(style, vgg)

    # Compute Gram matrices for style features
    style_grams = {layer: gram_matrix(style_features[layer]) for layer in style_features}

    # Initialize target image as content image
    target = content.clone().requires_grad_(True).to(device)

    # Define optimizer
    optimizer = optim.Adam([target], lr=0.003)

    # Define loss function
    style_weights = {'conv1_1': 0.1, 'conv2_1': 0.2, 'conv3_1': 0.4, 'conv4_1': 0.3, 'conv5_1': 0.1}

    for step in range(steps):
        target_features = get_features(target, vgg)

        # Compute content loss
        content_loss = torch.mean((target_features['conv4_2'] - content_features['conv4_2']) ** 2)

        # Compute style loss
        style_loss = 0
        for layer in style_weights:
            target_gram = gram_matrix(target_features[layer])
            style_gram = style_grams[layer]
            _, d, h, w = target_features[layer].shape
            layer_style_loss = style_weights[layer] * torch.mean((target_gram - style_gram) ** 2) / (d * h * w)
            style_loss += layer_style_loss

        total_loss = alpha * content_loss + beta * style_loss

        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        if step % 50 == 0:
            print(f"Step {step}/{steps}, Total Loss: {total_loss.item()}")

    # Convert tensor to image
    output_image = target.detach().cpu().squeeze(0).permute(1, 2, 0).numpy()
    output_image = np.clip(output_image, 0, 1)  # Proper normalization

    plt.imsave(output_path, output_image)

    return output_path
