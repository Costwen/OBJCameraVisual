import os
import open3d
import argparse
import json
import numpy as np
def main(args):
    WIDTH = 1280
    HEIGHT = 720
    vizualizer = open3d.visualization.Visualizer()
    vizualizer.create_window()
    vizualizer.create_window(width=WIDTH, height=HEIGHT)
    model_path = args.model_path
    # load obj
    mesh = open3d.io.read_triangle_mesh(model_path, enable_post_processing=True)
    aabb = mesh.get_axis_aligned_bounding_box()
    center = aabb.get_center()
    extents = aabb.get_extent()

    scale_factor = 2 / np.max(extents)

    mesh.translate(-center)
    mesh.scale(scale_factor, center=[0, 0, 0])

    if not mesh.has_vertex_normals():
        mesh.compute_vertex_normals()
    vizualizer.add_geometry(mesh)
    meta = json.load(open(args.camera_path, 'r'))

    fov = meta["camera_angle_x"]
    image_size = 1
    focal_length = 0.5*image_size / np.tan(0.5 * fov) 

    intrinsics = np.array(
        [
            [focal_length, 0, image_size/2],
            [0, focal_length, image_size/2],
            [0, 0, 1],
        ],
        dtype=np.float32,
    )
    c2w_list = []
    for item in meta['locations']:
        c2w = np.array(item['transform_matrix'])
        c2w[:, 1:3] *= -1 # blender to opencv
        if args.add_axis:
            axis = open3d.geometry.TriangleMesh.create_coordinate_frame(size=0.05, origin=[0, 0, 0])
            axis.rotate(c2w[:3, :3])
            axis.translate(c2w[:3, 3])
            vizualizer.add_geometry(axis)
        c2w[:, 3] *= 10
        c2w = np.linalg.inv(c2w)
        c2w_list.append(c2w)
    
    view_point = np.array([0, -2, 0])  # maybe change this
    distance_list = []
    for c2w in c2w_list:
        cameraLines = open3d.geometry.LineSet.create_camera_visualization(view_width_px=1, view_height_px=1, intrinsic=intrinsics, extrinsic=c2w)
        line_center = np.mean(np.asarray(cameraLines.points), axis=0)
        distance = np.linalg.norm(line_center - view_point)
        distance_list.append(distance)

    min_dis = min(distance_list)
    max_dis = max(distance_list)

    for c2w in c2w_list:
        cameraLines = open3d.geometry.LineSet.create_camera_visualization(view_width_px=1, view_height_px=1, intrinsic=intrinsics, extrinsic=c2w)
        line_center = np.mean(np.asarray(cameraLines.points), axis=0)
        distance = np.linalg.norm(line_center - view_point)
        distance = (distance - min_dis)/ (max_dis - min_dis)
        color_value = np.array([0, 0, 0])  + np.log(distance + 1)
        num_lines = np.asarray(cameraLines.lines).shape[0]
        colors = [color_value for _ in range(num_lines)]
        cameraLines.colors = open3d.utility.Vector3dVector(colors)
        vizualizer.add_geometry(cameraLines)
           
    vizualizer.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="model.obj")
    parser.add_argument("--camera_path", type=str, default="meta.json")
    parser.add_argument("--add_axis", type=bool, default=False)
    args = parser.parse_args()
    main(args)
