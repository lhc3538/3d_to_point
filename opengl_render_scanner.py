import random

import numpy as np
import scipy.misc

import color_tool as color_t
import obj_tool as objt
import points_tool as ptst
import renderer as renderer
import data_utils as du


def vscan(model, sample_ratio, camera_position, camera_lookat, camera_up, im_size=(400, 400), clip_near_set=10.0,
          clip_far_set=25.0, save_vis=True):
    print('vscan samplerate:', sample_ratio)
    print("\nVirtualScan: camera_position:", camera_position, "camera_lookat: ", camera_lookat, "camera_up", camera_up)

    R, T, RT = renderer.Compute_RT_LU([0, 0, 0], camera_lookat, camera_up, True)

    # print "Camera R:"
    # print R
    # print "Camera T:"
    # print T

    objt.obj_trans(model, [-camera_position[0], -camera_position[1], -camera_position[2]], False)

    # For Test
    # objt.save_obj(model,"./out/bftrans.obj")

    K = np.array([1000.0, 0.0, im_size[0] / 2, 0.0, 1000.0, im_size[1] / 2, 0.0, 0.0, 1.0]).reshape((3, 3))

    if save_vis:

        ## Render
        ren_rgb, ren_depth = renderer.render(model, im_size, K, R, T, mode='rgb+depth', clip_near=clip_near_set + 0.05,
                                             clip_far=clip_far_set)

        ## Save the visualization
        vis_rgb = ren_rgb.astype(np.float)
        vis_rgb = vis_rgb.astype(np.uint8)

        vis_depth = ren_depth.astype(np.float)
        # scale to [0,1]
        d_max = np.max(vis_depth)
        d_min = np.min(vis_depth)
        vis_depth = 255 * (vis_depth - d_min) / (d_max - d_min)
        vis_depth = vis_depth.astype(np.uint8)

        vis_rgb[vis_rgb > 255] = 255
        vis_depth[vis_depth > 255] = 255

        # save vis img
        scipy.misc.imsave("./out.png", vis_rgb.astype(np.uint8))
        scipy.misc.imsave("./out_d.png", vis_depth.astype(np.uint8))

    else:

        ren_depth = renderer.render(model, im_size, K, R, T, mode='depth', clip_near=clip_near_set + 0.05,
                                    clip_far=clip_far_set)

    # scan the point cloud
    visable_point = []
    visable_point_s = []
    scan_points = []
    scan_points_seg = []
    scan_points_label = []

    for i in range(im_size[0]):

        for k in range(im_size[1]):

            # print i,k,ren_depth[i][k]

            if ren_depth[i][k][0] - 0 > 0.0001:
                # print i,k,ren_depth[i][k]

                visable_point.append(
                    [i, k, ren_depth[i][k][0], ren_depth[i][k][1], ren_depth[i][k][2], ren_depth[i][k][3]])

    visable_num = len(visable_point)
    sample_num = int(visable_num * sample_ratio)

    print("visable_num:", visable_num, "/", im_size[0] * im_size[1], "Sample ratio:", sample_ratio, "Sample num:",
          sample_num)

    samplelist = random.sample(range(visable_num - 1), sample_num)

    for s_index in samplelist:
        visable_point_s.append(visable_point[s_index][:3])
        scan_points_seg.append((int(round(visable_point[s_index][3] * 255, 0)),
                                int(round(visable_point[s_index][4] * 255, 0)),
                                int(round(visable_point[s_index][5] * 255, 0))))
        scan_points_label.append(
            color_t.color_to_id([visable_point[s_index][3], visable_point[s_index][4], visable_point[s_index][5]]))

    # compute the world coordinate
    for pt_c in visable_point_s:
        # print "Process",pt_c

        # pt_c = [213, 526, 11.59547]
        # pt_w = [[10.12],[3.67],[-1.59],[1.0]]

        xcam = K[0][2]
        ycam = K[1][2]

        fx = K[0][0]
        fy = K[1][1]

        x_c_p = pt_c[1] - xcam
        y_c_p = -(pt_c[0] - ycam)
        z_c = pt_c[2]

        x_c = x_c_p * z_c / fx
        y_c = y_c_p * z_c / fy

        # print "camera coordinate:",x_c,y_c,z_c

        point_c = [[x_c], [y_c], [z_c], [1.0]]

        RT_M = np.mat(RT)

        point_w = np.dot(RT_M.I, point_c)

        # print
        x_w = float(point_w[0])
        y_w = float(point_w[1])
        z_w = float(point_w[2])

        # print "world coordinate:",x_w,y_w,z_w

        scan_points.append([x_w, y_w, z_w])

    objt.obj_trans(model, camera_position, False)
    ptst.pc_trans(scan_points, camera_position, False)

    # ptst.save_ply(scan_points, scan_point_seg, "vis.ply")

    return scan_points, scan_points_seg, scan_points_label


def virtualscan(model, scan_points, sample_rate):
    scan_set_list = []
    scan_point_list = []
    # clip_near = 100
    # clip_far = 150
    clip_near = 2
    clip_far = 100
    im_size = (384, 384)

    for scp in scan_points:
        # front
        # scan_set_list.append([scp[0], scp[1], scp[2] + clip_near, 0.0, 0.0, -1.0, 0.0, 1.0, 0.0])
        # Back
        # scan_set_list.append([scp[0], scp[1], scp[2] - clip_near, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0])
        # left
        # scan_set_list.append([scp[0] - clip_near, scp[1], scp[2], 1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        # right use this
        scan_set_list.append([scp[0] + clip_near, scp[1], scp[2], -1.0, 0.0, 0.0, 0.0, 1.0, 0.0])


    # scan_ori = random.randint(0,1)
    # add_scan = 0
    # scan_h = 0.4 + random.randint(0,12)*1.0/10
    # scan_h_l = 0.2 + random.randint(0,10)*1.0/10
    # scan_h_h = 1.3 + random.randint(0,10)*1.0/10

    # if scan_ori:

    #	if add_scan:
    #		#front
    #		scan_set_list.append([scp[0],scan_h_l,scp[1] + clip_near,0.0,0.0,-1.0,0.0,1.0,0.0])
    #		scan_set_list.append([scp[0],scan_h_h,scp[1] + clip_near,0.0,0.0,-1.0,0.0,1.0,0.0])
    #		#Back
    #		scan_set_list.append([scp[0],scan_h_l,scp[1] - clip_near,0.0,0.0,1.0,0.0,1.0,0.0])
    #		scan_set_list.append([scp[0],scan_h_h,scp[1] - clip_near,0.0,0.0,1.0,0.0,1.0,0.0])

    #	else:
    #		#front
    #		scan_set_list.append([scp[0],scan_h,scp[1] + clip_near,0.0,0.0,-1.0,0.0,1.0,0.0])
    #		#Back
    #		scan_set_list.append([scp[0],scan_h,scp[1] - clip_near,0.0,0.0,1.0,0.0,1.0,0.0])

    # else:

    #	if add_scan:
    #		#left
    #		scan_set_list.append([scp[0] - clip_near,scan_h_l,scp[1],1.0,0.0,0.0,0.0,1.0,0.0])
    #		scan_set_list.append([scp[0] - clip_near,scan_h_h,scp[1],1.0,0.0,0.0,0.0,1.0,0.0])
    #		#right
    #		scan_set_list.append([scp[0] + clip_near,scan_h_l,scp[1],-1.0,0.0,0.0,0.0,1.0,0.0])
    #		scan_set_list.append([scp[0] + clip_near,scan_h_h,scp[1],-1.0,0.0,0.0,0.0,1.0,0.0])

    #	else:
    #		#left
    #		scan_set_list.append([scp[0] - clip_near,scan_h,scp[1],1.0,0.0,0.0,0.0,1.0,0.0])
    #		#right
    #		scan_set_list.append([scp[0] + clip_near,scan_h,scp[1],-1.0,0.0,0.0,0.0,1.0,0.0])

    for k, scset in enumerate(scan_set_list):
        camera_position = [scset[0], scset[1], scset[2]]
        camera_lookat = [scset[3], scset[4], scset[5]]
        camera_up = [scset[6], scset[7], scset[8]]

        # For Test
        # camera_position = [25.5,7.5,60.5]
        # camera_lookat = [0.0,0.0,-1.0]
        # camera_up = [0.0,1.0,0.0]

        scan_points, scan_points_seg, scan_points_label = vscan(model, sample_rate, camera_position, camera_lookat,
                                                                camera_up, im_size, clip_near, clip_far, save_vis=True)

        scan_point_list.append([scan_points, scan_points_seg, scan_points_label])

    # For Test
    # ptst.save_ply(scan_points_m, scan_point_seg, "./output/vis_" + str(k) + ".ply")

    # merge
    scan_points_m, scan_points_seg_m, scan_points_label_m = ptst.scan_pc_merge(scan_point_list)

    # For Test
    # ptst.save_ply(scan_points_m, scan_points_seg_m, "./output/vis.ply")

    return scan_points_m, scan_points_seg_m, scan_points_label_m


def test():
    # plane
    # model = objt.load_ply("/home/leon/Disk/dataset/Downloads/ShapeNetCore/ShapeNetCore.v2/02691156/"
    #                       "1a04e3eab45ca15dd86060f189eb133/models/model_normalized.ply")
    # car1
    model = objt.load_ply("/home/leon/Disk/dataset/ShapeNetCar/02958343/1a0bc9ab92c915167ae33d942430658c/"
                          "models/model_normalized.ply")
    # cup
    # model = objt.load_obj("/home/leon/Disk/dataset/Downloads/ShapeNetCore/ShapeNetCore.v2/03797390/"
    #                       "1a1c0a8d4bad82169f0594e65f756cf5/models/model_normalized.obj")

    # car2
    # model = objt.load_ply("/home/leon/Disk/dataset/ShapeNetCar/02958343/1a1dcd236a1e6133860800e6696b8284/"
    #                       "models/model_normalized.ply")

    # scan obj
    # compute scan point TODO config and random point
    scan_point = []
    obj_bbox = objt.obj_getbbox(model['pts'])
    print(obj_bbox)

    # center
    # scan_point.append([(obj_bbox[0] + obj_bbox[1]) / 2, (obj_bbox[2] + obj_bbox[3]) / 2, (obj_bbox[4] + obj_bbox[5]) / 2])
    # boundary
    # scan_point.append([obj_bbox[0], (obj_bbox[2] + obj_bbox[3]) / 2, (obj_bbox[4] + obj_bbox[5]) / 2])
    scan_point.append([obj_bbox[1] + 5, (obj_bbox[2] + obj_bbox[3]) / 2, (obj_bbox[4] + obj_bbox[5]) / 2])
    # scan_point.append([(obj_bbox[0] + obj_bbox[1]) / 2, (obj_bbox[2] + obj_bbox[3]) / 2, obj_bbox[4]])
    # scan_point.append([(obj_bbox[0] + obj_bbox[1]) / 2, (obj_bbox[2] + obj_bbox[3]) / 2, obj_bbox[5]])
    # random
    # for i in range(scan_point_num):
    # scan_point.append([random.uniform(obj_bbox[0],obj_bbox[1]),random.uniform(obj_bbox[2],obj_bbox[3]),random.uniform(obj_bbox[4],obj_bbox[5])])

    scan_points, scan_points_seg, scan_points_label = virtualscan(model, scan_point, 0.9)
    # print(len(scan_points))
    du.save_dataset(scan_points, scan_points_seg, scan_points_label, "sense_name", "pts", "seg", "plyshow", save_ply=True,
                    use_color_map=False)


if __name__ == '__main__':
    test()