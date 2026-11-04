import cv2
import numpy as np

def blend_patch(base, patch, mask, center):
    # center is (x, y)
    return cv2.seamlessClone(patch, base, mask, center, cv2.NORMAL_CLONE)

def main():
    s04 = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_scene_04_fixed_canon.png')
    s06 = cv2.imread(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\anime_scene_06.png')

    h, w = s06.shape[:2]
    canvas = s06.copy()

    # 1. FEET REPLACEMENT
    # In s04, Elena's dress hem is at y~600, feet reach y~740.
    # Feet in s04: bbox [590:750, 710:830]
    # In s06, Elena's feet are around [600:755, 785:875]
    feet_s04 = s04[585:755, 700:840].copy()
    
    # Let's resize feet_s04 slightly if needed to match s06 leg width
    # In s06: legs start at dress hem y~600. Dress hem is around x: 775 to 870
    target_w = 110
    target_h = 160
    feet_resized = cv2.resize(feet_s04, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    
    # Color match feet: adjust cobblestone lighting slightly to match s06 cool blue/warm lamplight
    # Create smooth elliptical/feathered mask
    mask_feet = np.zeros((target_h, target_w), dtype=np.uint8)
    cv2.ellipse(mask_feet, (target_w // 2, target_h // 2), (target_w // 2 - 4, target_h // 2 - 4), 0, 0, 360, 255, -1)
    mask_feet = cv2.GaussianBlur(mask_feet, (15, 15), 0)

    # Place feet at (x_center=830, y_center=680)
    # Let's do alpha blend with feathered mask
    x1, y1 = 830 - target_w // 2, 680 - target_h // 2
    x2, y2 = x1 + target_w, y1 + target_h
    
    alpha = (mask_feet.astype(np.float32) / 255.0)[:, :, None]
    roi = canvas[y1:y2, x1:x2].astype(np.float32)
    blended_feet = (feet_resized.astype(np.float32) * alpha + roi * (1.0 - alpha)).astype(np.uint8)
    canvas[y1:y2, x1:x2] = blended_feet

    cv2.imwrite(r'd:\Projects\VideoGenerator\moy_mir_iz_snov_frames\s06_step1_feet.png', canvas)
    print("Step 1 (feet) saved")

if __name__ == '__main__':
    main()
