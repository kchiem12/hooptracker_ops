'''
Court Detection and Rendering Module
'''
import os
import cv2 as cv
import numpy as np
import random


class Bin:
    'Bin to store color ranges of two channels'
    def __init__(self, value, one_lower:int, one_upper:int, two_lower:int, two_upper:int):
        self.one_lower = one_lower
        self.one_upper = one_upper
        self.two_lower = two_lower
        self.two_upper = two_upper
        self.value = value

    def __str__(self):
        return 'Bin('+str(round(self.value,3))+','+str(self.one_lower)+','+str(self.one_upper)+','+str(self.two_lower)+','+str(self.two_upper)+')'


class Render:
    '''
    Object which, given video input and state data,
    will produce video court visualization of player positions.
    '''
    def __init__(self, video_path:str, display_images:bool=False):
        '''
        Runs court detection on video input
        @param video_path is path from project root to video file
        @param display_images determines whether or not to display images for debugging
        '''
        self._TRUE_PATH = os.path.join('data','true_map.png')
        self._VIDEO_PATH = video_path
        self._BINNING_THRESHOLD = 0.001
        'Minimum percentage of pixels to be included in list of color bins'
        self._COLOR_SMOOTHING = 5
        'Padding to be added to selected HSV to include more color range'
        self._HALF_COURT_BOUNDS = np.array([(2043,1920),(2043,35),(37,35),(37,1920)])
        'Coordinates of four corners of truth map counterclock starting from bottom right'
        self._BOX_BOUNDS = np.array([(1277,798),(1277,35),(803,35),(803,798)])
        'Coordinates of four corners of inner box counterclock starting from bottom right'
        video = cv.VideoCapture(self._VIDEO_PATH)
        _, self._BGR_COURT = video.read()
        self._YCRCB_COURT = cv.cvtColor(self._BGR_COURT,cv.COLOR_BGR2YCrCb)
        'User court in YCrCb color space'
        self._HSV_COURT = cv.cvtColor(self._BGR_COURT, cv.COLOR_BGR2HSV)
        'User court in HSV color space'
        self._GRAY_COURT = cv.cvtColor(self._BGR_COURT, cv.COLOR_BGR2GRAY)
        'User court in gray scale'
        self._MASK_COURT_EDGES = self._GRAY_COURT.copy() # temp assignment
        'Final processed image of court edges'
        self._TRUTH_COURT_MAP = cv.imread(self._TRUE_PATH,cv.IMREAD_GRAYSCALE)
        'True court map of half court'


        # Downsample truth map
        height, width = self._TRUTH_COURT_MAP.shape[:2]
        new_height = int(height/2)
        new_width = int(width/2)
        self._BOX_BOUNDS = self._BOX_BOUNDS/2
        self._TRUTH_COURT_MAP = cv.resize(self._TRUTH_COURT_MAP, (new_width, new_height))

        self._HSV_BINNING = True # choose either HSV binning or YCrCb binning
        if self._HSV_BINNING:
            self._index = (0,1)
            self._one_max = 180.0
            self._two_max = 256.0
            self._COURT_IMG = self._HSV_COURT
        else:
            self._index = (1,2)
            self._one_max = 256.0
            self._two_max = 256.0
            self._COURT_IMG = self._YCRCB_COURT

        self._HOMOGRAPHY = None
        'Homography matrix to transform court to minimaped version'

        if display_images:
            self._HOMOGRAPHY = self._detect_courtlines_and_display()
        else:
            self._HOMOGRAPHY = self._detect_courtlines()

    def get_homography(self):
        return self._HOMOGRAPHY


    def _detect_courtlines(self):
        'Finds best homography'
        bins = self._bin_pixels(self._COURT_IMG, one_bins=18, two_bins=10)
        mask = self._get_mask(self._COURT_IMG, bins[0])
        canny_edges = self._get_canny(self._GRAY_COURT)
        masked_edges = self._apply_mask(canny_edges, mask)
        hough_lines = self._get_hough(masked_edges,threshold=180)
        thick_masked_edges = self._thicken_edges(masked_edges,iterations=1)
        self._MASK_COURT_EDGES = thick_masked_edges.copy()
        best_pts = self._find_best_homography(hough_lines)
        while True:
            if not self._regress_box_boundary(best_pts):
                break
        while True:
            if not self._fine_regress_box_boundary(best_pts):
                break
        homography, _ = cv.findHomography(np.array(best_pts),self._BOX_BOUNDS)
        return homography

    def _detect_courtlines_and_display(self):
        'Finds best homography and displays images of progress'
        bins = self._bin_pixels(self._COURT_IMG, one_bins=18, two_bins=10)
        mask = self._get_mask(self._COURT_IMG, bins[0])
        canny_edges = self._get_canny(self._GRAY_COURT)
        masked_edges = self._apply_mask(canny_edges, mask)
        masked_bgr = self._apply_mask(self._BGR_COURT, mask)
        hough_lines = self._get_hough(masked_edges,threshold=180)
        hough = self._apply_hough(self._BGR_COURT, hough_lines)
        thick_masked_edges = self._thicken_edges(masked_edges,iterations=1)
        self._MASK_COURT_EDGES = thick_masked_edges.copy()
        best_pts = self._find_best_homography(hough_lines)
        while self._regress_box_boundary(best_pts):
            print('new goodness',self._evaluate_homography(best_pts,self._BOX_BOUNDS))
        print('to fine tuning')
        while self._fine_regress_box_boundary(best_pts):
            print('new goodness',self._evaluate_homography(best_pts,self._BOX_BOUNDS))
        homography, _ = cv.findHomography(np.array(best_pts),self._BOX_BOUNDS)

        test_bgr = self._BGR_COURT.copy()
        color_map = cv.cvtColor(self._TRUTH_COURT_MAP,cv.COLOR_GRAY2BGR)
        colors = [(0,0,255),(0,255,0),(255,0,0), (255,255,0)]
        for i in range(0,4):
            pt = best_pts[i]
            cv.circle(test_bgr,(int(pt[0]),int(pt[1])), 5, colors[i], -1)
            pt = self._BOX_BOUNDS[i]
            cv.circle(color_map,(int(pt[0]),int(pt[1])), 10, colors[i], -1)
        new_img = self._apply_bgr_homography(self._BGR_COURT,best_pts)
        new_gray_img = self._apply_gray_homography(self._MASK_COURT_EDGES,best_pts,or_mask=True)
        second_gray_img = self._apply_gray_homography(self._MASK_COURT_EDGES,best_pts,or_mask=False)


        cv.imshow('original', self._BGR_COURT)
        cv.imshow('mask', mask)
        cv.imshow('canny', canny_edges)
        cv.imshow('canny masked', masked_edges)
        cv.imshow('bgr masked', masked_bgr)
        cv.imshow('hough transform', hough)
        cv.imshow('new test', new_img)
        cv.imshow('gray union', new_gray_img)
        cv.imshow('gray intersection', second_gray_img)
        cv.imshow('points image', test_bgr)
        cv.imshow('true map',color_map)

        # self._test_many_bins(self._COURT_IMG,self._BGR_COURT,bins,iterations=6)

        if cv.waitKey(0) & 0xff == 27:
            cv.destroyAllWindows()

        return homography

    def _bin_pixels(self,img:np.ndarray, one_bins:int=16, two_bins:int=16):
        '''
        Returns top bins from YCrCb color space
        @Param: img, image of court, either HSV or YCrCb depending on settings
        @param one_bins, number of bins of first channel
        @param two_bins, number of bins of second channel
        @returns: sorted array of most frequent color bin objects
        '''
        # generate weights
        weights = np.zeros((img.shape[0],img.shape[1]))
        for row in range(weights.shape[0]):
            row_weight = np.full(weights.shape[1], row)
            weights[row] = row_weight
        for col in range(weights.shape[1]):
            col_weight = np.full(weights.shape[0], min(col+1,weights.shape[1]-col))
            weights[:,col] = np.minimum(weights[:,col],col_weight)
        weights = weights/np.sum(weights)

        # split image pixels into bins
        bins = np.zeros((one_bins,two_bins))
        one_step = self._one_max / one_bins
        two_step = self._two_max / two_bins
        for row in range(img.shape[0]):
            for col in range(img.shape[1]):
                pix = img[row,col]
                bins[int(pix[self._index[0]]/one_step),
                     int(pix[self._index[1]]/two_step)] += weights[row,col]

        # sort bins
        top_bins = []
        for row in range(bins.shape[0]):
            for col in range(bins.shape[1]):
                if (bins[row,col] <= self._BINNING_THRESHOLD):
                    continue
                top_bins.append(Bin(bins[row,col],
                                int(round(one_step*row)),
                                int(round(one_step*(row+1))),
                                int(round(two_step*col)),
                                int(round(two_step*(col+1)))))
        return sorted(top_bins, reverse=True, key=lambda bin: bin.value)

    def _get_mask(self,img:np.ndarray, bin:Bin, morph:bool=True):
        '''
        Applies color range from specified bin
        @param img, image of court in same color space from Bin
        @param bin, bin of colors to mask image over
        @param morph, whether or not to process image to eliminate noise and holes
        @returns masked image
        '''
        # get mask
        lowerbound = np.full(3,0)
        upperbound = np.full(3,255)
        lowerbound[self._index[0]] = bin.one_lower - self._COLOR_SMOOTHING*1
        lowerbound[self._index[1]] = bin.two_lower - self._COLOR_SMOOTHING*1
        upperbound[self._index[0]] = bin.one_upper + self._COLOR_SMOOTHING*0
        upperbound[self._index[1]] = bin.two_upper + self._COLOR_SMOOTHING*0
        mask = cv.inRange(img, lowerbound, upperbound)

        # close and open mask
        if morph:
            kernel = np.ones((3,3),np.uint8)
            mask = cv.morphologyEx(mask,cv.MORPH_CLOSE,kernel,iterations=8) #get all court
            mask = cv.morphologyEx(mask,cv.MORPH_OPEN,kernel,iterations=30) #remove distractions
        return mask

    def _apply_mask(self,img:np.ndarray, mask:np.ndarray):
        '''
        Applies bitwise and mask
        @param img, image to mask over
        @param mask, mask, should be in grayscale
        @returns masked image
        '''
        return cv.bitwise_and(img,img,mask=mask)

    def _get_canny(self,img:np.ndarray, threshold1:int=10, threshold2:int=100):
        '''
        Applies Canny edge detection to image
        @param img, image of court in grayscale
        @param threshold1, threshold2, thresholds for Canny
        @return image of court edges
        '''
        return cv.Canny(img,threshold1,threshold2)

    def _thicken_edges(self,img:np.ndarray, iterations:int=2):
        '''
        Thickens the edges in an image
        @param img, grayscale image of court edges
        @param iterations, severity of thickness
        @returns image with thicker court edges
        '''
        kernel = np.ones((3,3),np.uint8)
        return cv.morphologyEx(img,cv.MORPH_DILATE,kernel,iterations=iterations)

    def _get_hough(self,img:np.ndarray,rho:float=1,theta:float=np.pi/180,threshold:int=200):
        '''
        Performs hough transform on image
        @param img, 8-bit grayscale image of court edges
        @returns list of lines detected given as rho and theta
        '''
        return cv.HoughLines(img, rho, theta, threshold)

    def _find_best_homography(self,lines:list):
        '''
        Finds best homography given list of lines
        @param lines, list of lines given by Hough Transform
        @returns list of four points corresponding to box boundary
        '''
        # divide into two classes of lines, sorted by rho
        # TODO: sort lines using k-means, k=2
        hor = lines[lines[:,0,1]<=np.pi/2] # baseline
        ver = lines[lines[:,0,1]>np.pi/2] # sideline
        hor = np.array(sorted(hor, key = lambda x : x[0][0]))
        ver = np.array(sorted(ver, key = lambda x : x[0][0]))
        return self._iterate_best_homography(hor,ver)

    def _iterate_best_homography(self,hor:list,ver:list,relax_factor=0):
        '''
        Iterates until best homography is found
        @param hor, ver, lists of lines grouped into two categories,
        likely to be lines parallel to each other.
        @param relax_factor, how much to relax constraints on homography points.
        @return four points, or None if no homography is found.
        '''
        max_goodness = 0
        max_homography = None
        for i1 in range(0,len(hor)):
            for i2 in range(i1+1,len(hor)):
                for j1 in range(len(ver)):
                    for j2 in range(j1+1,len(ver)):
                        pts = self._get_four_intersections(hor[i2][0],ver[j1][0],hor[i1][0],
                                                           ver[j2][0],relax_factor=relax_factor)
                        if pts is None:
                            continue
                        goodness = self._evaluate_homography(pts,self._BOX_BOUNDS)
                        if (goodness > max_goodness):
                            max_goodness = goodness
                            max_homography = pts

                        pts = self._get_four_intersections(ver[j2][0],hor[i2][0],ver[j1][0],
                                                           hor[i1][0],relax_factor=relax_factor)
                        if pts is None:
                            continue
                        goodness = self._evaluate_homography(pts,self._BOX_BOUNDS)
                        if (goodness > max_goodness):
                            max_goodness = goodness
                            max_homography = pts
        if max_homography is None:
            if relax_factor > 2:
                return None
            return self._iterate_best_homography(hor,ver,relax_factor=relax_factor+0.25)
        return max_homography

    def _evaluate_homography(self,pts_src:list,pts_dst:list):
        '''
        Evalues how well a homography performs on court
        @param pts_src, four points on court image of box, counterclockwise
        @param pts_src, four points on true image of court to map toz
        @return goodness, proportion of intersection.
        '''
        assert(pts_src is not None)
        mapped_edge_img = self._apply_gray_homography(self._MASK_COURT_EDGES,pts_src,pts_dst=pts_dst)
        total_max_overlap = self._max_pixel_overlap(self._MASK_COURT_EDGES,pts_src,pts_dst=pts_dst)
        goodness = float(np.count_nonzero(mapped_edge_img > 100)) / total_max_overlap
        return goodness

    def _get_four_intersections(self,l1:list,l2:list,l3:list,l4:list,relax_factor=0):
        '''
        Gets four points from intersection of four lines.
        @param l1, line by free throw line
        @param l2, l3, l4, lines going counterclockwise around box
        @param relax_factor, how much to relax restriction for image size
        @returns four points going counterclockwise, or None is points are not valid
        '''
        p1 = self._get_line_intersection(l1,l2)
        p2 = self._get_line_intersection(l2,l3)
        p3 = self._get_line_intersection(l3,l4)
        p4 = self._get_line_intersection(l4,l1)
        d1 = self._distance(p1,p2)
        d2 = self._distance(p2,p3)
        d3 = self._distance(p3,p4)
        d4 = self._distance(p4,p1)
        relax = 1000*relax_factor
        if (d1<600-relax or d1>800+relax or d3<600-relax or d3>800+relax or d2<50 or
            d2>300+relax or d4<50 or d4>300+relax or self._is_not_convex(p1,p2,p3,p4)):
            return None
        return (p1,p2,p3,p4)

    def _get_line_intersection(self,line1:list,line2:list):
        '''
        Gets intersection of two lines.
        @param line1, line2, lines given in form (rho,theta)
        @return point (x,y) of their intersection, or (0,0) if parallel
        '''
        rho1, theta1 = line1
        rho2, theta2 = line2
        a1 = np.cos(theta1)
        a2 = np.sin(theta1)
        b1 = np.cos(theta2)
        b2 = np.sin(theta2)
        d = a1*b2 - a2*b1
        if d==0:
            return (0,0)
        x = (rho1*b2-rho2*a2) / d
        y = (-rho1*b1+rho2*a1) / d
        return (x,y)

    def _distance(self,pt1:list,pt2:list):
        '''
        @param pt1, pt2, points given as (x,y) in pixels
        @returns Euclidean distnace between points
        '''
        return ((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)**0.5

    def _is_not_convex(self,*pts:list):
        '''
        Checks if set of points is convex
        @param *pts, set of points given in order and as (x,y)
        @returns True, if not convex, False if convex
        '''
        N = len(pts)
        prev, curr = 0, 0
        for i in range(N):
            temp = [pts[i],pts[(i+1)%N],pts[(i+2)%N]]
            curr = self._cross_product(temp)
            if curr != 0:
                if curr * prev < 0:
                    return True
                else:
                    prev = curr
        return False

    def _cross_product(self,A:list):
        '''
        @param A, list of 3 vectors of dim 2
        @returns cross product of 2 vectors
        '''
        X1 = (A[1][0] - A[0][0])
        Y1 = (A[1][1] - A[0][1])
        X2 = (A[2][0] - A[0][0])
        Y2 = (A[2][1] - A[0][1])
        return (X1 * Y2 - Y1 * X2)

    def _regress_box_boundary(self,pts_src,delta=range(1,40)):
        '''
        Adjust box boundary to get better homography
        @param pts_src, list of four points of box boundary, counterclockwise
        @param delta, amount to change court boundary
        @returns True, if box boundary was adjusted, and False otherwise
        '''
        if pts_src is None:
            return False
        prev_good = self._evaluate_homography(pts_src,self._BOX_BOUNDS)
        box_bounds = []
        for i in [0]:
            for j in [-1,1]:
                for d in delta:
                    # copy = self.BOX_BOUNDARY.copy()
                    # copy[i:i+2,0] += delta*j
                    # box_bounds.append(copy)
                    copy = self._BOX_BOUNDS.copy()
                    copy[[i-1,i],1] += d*j
                    box_bounds.append(copy)

        max_good = 0
        max_index = 0
        for i in range(len(box_bounds)):
            good = self._evaluate_homography(pts_src,box_bounds[i])
            if good > max_good:
                max_good = good
                max_index = i

        if max_good <= prev_good:
            return False
        else:
            self._BOX_BOUNDS = box_bounds[max_index]
            return True

    def _fine_regress_box_boundary(self,pts_src,delta=range(1,5)):
        '''
        Finely adjust box boundary to get better homography
        @param pts_src, list of four points of box boundary, counterclockwise
        @param delta, amount to change court boundary
        @returns True, if box boundary was adjusted, and False otherwise
        '''
        if pts_src is None:
            return False
        prev_good = self._evaluate_homography(pts_src,self._BOX_BOUNDS)
        box_bounds = []
        for i in [0,1,2,3]:
            for j in [0,1]:
                epsilon = random.random()
                for k in [-epsilon,epsilon]:
                    for d in delta:
                        copy = self._BOX_BOUNDS.copy()
                        copy[i,j] += d*k
                        box_bounds.append(copy)

        max_good = 0
        max_index = 0
        for i in range(len(box_bounds)):
            good = self._evaluate_homography(pts_src,box_bounds[i])
            if good > max_good:
                max_good = good
                max_index = i

        if max_good <= prev_good*1.00001:
            return False
        else:
            self._BOX_BOUNDS = box_bounds[max_index]
            return True

    def _apply_hough(self,img:np.ndarray, lines:list):
        '''
        Draws lines from hough transformation onto image
        @param img, bgr image of court
        @param lines, list of lines given by Hough Transform
        @returns image with lines drawn on
        '''
        out = img.copy()
        for line in lines:
            rho, theta = line[0]
            a, b = np.cos(theta), np.sin(theta)
            x0, y0 = a*rho, b*rho
            x1, y1 = int(x0 + 2000*(-b)), int(y0 + 2000*(a))
            x2, y2 = int(x0 - 2000*(-b)), int(y0 - 2000*(a))
            cv.line(out,(x1,y1),(x2,y2),[0,0,255])
        return out


    def _apply_gray_homography(self,im_src:np.ndarray, pts_src:list, pts_dst=None, or_mask=False):
        '''
        Return warped image given list of four pts
        @Preconditions: im_src is grayscale image of masked edges
        src_pts: list of fours (x,y)* starting at back right corner of box and looping around counterclockwise
        or_mask: lets us see all parts of both truth map and homographied image
        '''
        im_dst = self._TRUTH_COURT_MAP.copy()
        if pts_dst is None:
            pts_dst = self._BOX_BOUNDS
        pts_src = np.array(pts_src)
        h, _ = cv.findHomography(pts_src,pts_dst)
        im_out = cv.warpPerspective(im_src, h, (im_dst.shape[1],im_dst.shape[0]))
        if or_mask:
            return cv.bitwise_or(im_out,self._invert_grayscale(im_dst))
        else:
            return cv.bitwise_and(im_out,self._invert_grayscale(im_dst))
    
    def _max_pixel_overlap(self,im_src:np.ndarray, pts_src:list, pts_dst=None):
        '''
        Returns max number of pixels homography can obtain given camera viewport
        @Preconditions: im_src is grayscale image of masked edges
        src_pts: list of fours (x,y)* starting at back right corner of box and looping around counterclockwise
        '''
        all_white = np.full_like(im_src,255)
        max_overlap = self._apply_gray_homography(all_white,pts_src,pts_dst=pts_dst)
        return np.count_nonzero(max_overlap > 100)

    def _apply_bgr_homography(self,im_src:np.ndarray, pts_src:list):
        '''
        Return warped bgr image given list of four pts
        @Preconditions: im_src is bgr image of court
        src_pts: list of fours (x,y)* starting at back right corner of box and looping around counterclockwise
        '''
        im_dst = self._TRUTH_COURT_MAP.copy()
        pts_dst = self._BOX_BOUNDS
        pts_src = np.array(pts_src)
        h, _ = cv.findHomography(pts_src,pts_dst)
        im_out = cv.warpPerspective(im_src, h, (im_dst.shape[1],im_dst.shape[0]))
        return cv.bitwise_or(im_out,cv.cvtColor(self._invert_grayscale(im_dst),cv.COLOR_GRAY2BGR))

    def _convert_to_hsv(self,img_path:str, img:np.ndarray=None):
        '''
        Helper function converts bgr image to HSV and separates into channels
        @param img_path, file path to source image
        @param img, bgr image of court if already read in
        @returns nothing, just displays separated color channels
        '''
        if img is None:
            img = cv.imread(img_path)

        hsv = cv.cvtColor(img,cv.COLOR_BGR2HSV)

        hue_only = hsv.copy()
        hue_only[:,:,1] = 255
        hue_only[:,:,2] = 255

        sat_only = hsv.copy()
        sat_only[:,:,0] = 0
        sat_only[:,:,2] = 255

        val_only = hsv.copy()
        val_only[:,:,0] = 0
        val_only[:,:,1] = 255

        hue_only = cv.cvtColor(hue_only, cv.COLOR_HSV2BGR)
        sat_only = cv.cvtColor(sat_only, cv.COLOR_HSV2BGR)
        val_only = cv.cvtColor(val_only, cv.COLOR_HSV2BGR)

        cv.imshow("Original", img)
        cv.imshow("Hue Only", hue_only)
        cv.imshow("Saturation Only", sat_only)
        cv.imshow("Value Only", val_only)

    def _convert_to_ycrcb(self,img_path:str, img:np.ndarray=None):
        '''
        Helper function converts bgr image to YCrCb and separates into channels
        @param img_path, file path to source image
        @param img, bgr image of court if already read in
        @returns nothing, just displays separated color channels
        '''
        if img is None:
            img = cv.imread(img_path)

        ycrcb = cv.cvtColor(img,cv.COLOR_BGR2YCrCb)

        luma_only = ycrcb.copy()
        luma_only[:,:,1] = 128
        luma_only[:,:,2] = 128

        blue_only = ycrcb.copy()
        blue_only[:,:,0] = 0
        blue_only[:,:,2] = 128

        red_only = ycrcb.copy()
        red_only[:,:,0] = 0
        red_only[:,:,1] = 128

        luma_only = cv.cvtColor(luma_only, cv.COLOR_YCrCb2BGR)
        blue_only = cv.cvtColor(blue_only, cv.COLOR_YCrCb2BGR)
        red_only = cv.cvtColor(red_only, cv.COLOR_YCrCb2BGR)

        cv.imshow("Original", img)
        cv.imshow("Luma Only", luma_only)
        cv.imshow("Blue Difference Only", blue_only)
        cv.imshow("Red Difference Only", red_only)

    def _invert_grayscale(self,gray_img:np.ndarray):
        '''
        Inverts grayscale images
        @param gray_img, gray scale image to invert.
        @returns inverted grayscale image
        '''
        ret = gray_img.copy()
        ret[ret[:,:] >= 128] = 128
        ret[ret[:,:] < 128] = 255
        ret[ret[:,:] == 128] = 0
        return ret

    def _test_many_bins(self,hsv:np.ndarray, bgr:np.ndarray, bins:list, iterations:int=6):
        '''
        Helper function to see what colors are in the bins
        @param hsv, hsv image of court
        @param bgr, bgr image of court
        @param bins, list of all color bins in order
        @param iterations, number of bins to test
        @returns nothing, just displays masking of bins on court image
        '''
        for i in range(min(iterations, len(bins))):
            mask = self._get_mask(hsv, bins[i], morph=False)
            masked = self._apply_mask(bgr,mask)
            cv.imshow('Bin Level ' + str(i+1), masked)

    def _test_many_canny(self,gray_img:np.ndarray, mask:np.ndarray, grid:list):
        '''
        Helper function to see different threshold levels of canny edge detection
        @param gray_img, grayscale image of court
        @param mask, mask over floor
        @param grid, list of tuples (one,two) for thresholds to test in canny
        @returns nothing, just display images of canny edges
        '''
        for one in grid:
            for two in grid:
                if one > two:
                    continue
                canny = self._get_canny(gray_img, threshold1=one, threshold2=two)
                masked_canny = self._apply_mask(canny, mask)
                cv.imshow(str(one)+' by '+str(two), masked_canny)

    def _test_many_hough(self,gray_img:np.ndarray, canny:np.ndarray, grid:list):
        '''
        Helper function to test many hough lines of different thresholds
        @param gray_img, grayscale image of court to draw on
        @param canny, image of court edges
        @param grid, list of floats for threshold values for hough transform
        '''
        for rho in grid[0]:
            for theta in grid[1]:
                for threshold in grid[2]:
                    lines = self._get_hough(canny, rho, theta, threshold)
                    hough = self._apply_hough(gray_img, lines)
                    cv.imshow(str(rho)+' by '+str(round(theta,3))+' by '+str(threshold), hough)

if __name__ == '__main__':
    video_path = os.path.join('data','training_data.mp4')
    render = Render(video_path=video_path,display_images=True)

    # x,y = 800,460
    # x1, y1 = render._transform_point(x,y)

    # print(x,y)
    # print("new homo",x1,y1)

    # filename = os.path.join('court','temp','point.mp4')
    # render.render_video(states,players,filename)
