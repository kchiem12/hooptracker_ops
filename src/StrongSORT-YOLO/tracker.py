from pathlib import Path
import track_v5
import pickle

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # yolov5 strongsort root directory
WEIGHTS = ROOT / 'weights'

def get_data(source_mov:str):
    """ returns dict as: {
        'basketball_data': (basketball_bounding_boxes, video_path),
        'person_data': (persons_and_rin_bounding_boxes, vide_path)
        }.

    Args:
        source_mov (string path): path to video file
    """
    out_array_pr, vid_path = track_v5.run(source = source_mov, classes= [1, 2],  yolo_weights = 
                                          WEIGHTS / 'best.pt', save_vid=False, ret=True)
    out_array_bb, bb_vid_path = track_v5.run(source = source_mov, 
                                             yolo_weights = WEIGHTS / 'best_basketball.pt', 
                                             save_vid=False, ret=True, skip_big=True)
    
    return {'basketball_data': (out_array_bb, bb_vid_path), 'person_data': (out_array_pr, vid_path)}


def test():
    print('import worked')

if __name__ == '__main__':
    output = get_data('../../data/benson.mp4')
    print(output['basketball_data'])
    with open('../../tmp/test_output.pickle', 'wb') as f:
        pickle.dump(output, f)
    