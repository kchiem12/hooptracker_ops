from pathlib import Path
import track_v5
import pickle
import multiprocessing as mp
import threading as th
import time

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # yolov5 strongsort root directory
WEIGHTS = ROOT / 'weights'

def track_person(res, source_mov:str, idx:int):
    """ tracks persons in video and puts data in out_queue"""
    out_array_pr, vid_path = track_v5.run(source = source_mov, classes= [1, 2],  yolo_weights = 
                                          WEIGHTS / 'best.pt', save_vid=False, ret=True)
    
    res[idx] = (out_array_pr, vid_path)

    print("==============Put data from tracking person and rim============")
    return

def track_basketball(res, source_mov:str, idx:int):
    """ tracks basketball in video and puts data in out_queue"""
    out_array_bb, bb_vid_path = track_v5.run(source = source_mov, 
                                             yolo_weights = WEIGHTS / 'best_basketball.pt', 
                                             save_vid=False, ret=True, skip_big=True)
    
    res[idx] = (out_array_bb, bb_vid_path)

    print("==============Put data from tracking basketball============")
    return

def get_data(source_mov:str):
    """ returns dict as: {
        'basketball_data': (basketball_bounding_boxes, video_path),
        'person_data': (persons_and_rim_bounding_boxes, vide_path)
        }.

    Args:
        source_mov (string path): path to video file
    """


    # ---------THREADING APPROACH---------------

    # res = [None] * 2

    # t1 = th.Thread(target=track_person, args=(res, source_mov, 0))
    # t2 = th.Thread(target=track_basketball, args=(res, source_mov, 1))

    # start = time.time()

    # t1.start()
    # t2.start()

    # t1.join()
    # t2.join()

    # out_array_pr, vid_path = res[0]
    # out_array_bb, bb_vid_path = res[1]

    # ---------MULTIPROCESSING APPROACH---------------

    res = mp.Manager().list([None] * 2)

    p1 = mp.Process(target=track_person, args=(res, source_mov, 0))
    p2 = mp.Process(target=track_basketball, args=(res, source_mov, 1))

    start = time.time()

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    out_array_pr, vid_path = res[0]
    out_array_bb, bb_vid_path = res[1]

    end = time.time()

    print(f'=============time elapsed: {end-start}=================')
    
    return {'basketball_data': (out_array_bb, bb_vid_path), 'person_data': (out_array_pr, vid_path)}


def test():
    print('import worked')

if __name__ == '__main__':
    # TODO change to actual video path
    output = get_data('../../data/training_data.mp4')
    print(output['basketball_data'])
    with open('../../tmp/test_output.pickle', 'wb') as f:
        pickle.dump(output, f)
    
