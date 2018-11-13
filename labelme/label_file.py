import base64
import json
import os.path
import sys

from ._version import __version__


PY2 = sys.version_info[0] == 2


class LabelFileError(Exception):
    pass


class LabelFile(object):

    suffix = '.json'

    def __init__(self, filename=None):
        self.shapes = ()
        self.imagePath = None
        self.imageData = None
        if filename is not None:
            self.load(filename)
        self.filename = filename

    def load(self, filename):
        keys = [
            'imageData',
            'imagePath',
            'lineColor',
            'fillColor',
            'shapes',  # polygonal annotations
            'flags',   # image level flags
            'imageSize',  # image size: [width, height]
        ]
        try:
            with open(filename, 'rb' if PY2 else 'r') as f:
                data = json.load(f)
            if data['imageData'] is not None:
                imageData = base64.b64decode(data['imageData'])
            else:
                # relative path from label file to relative path from cwd
                imagePath = os.path.join(os.path.dirname(filename),
                                         data['imagePath'])
                with open(imagePath, 'rb') as f:
                    imageData = f.read()
            flags = data.get('flags')
            imagePath = data['imagePath']
            if 'imageSize' in data:
                imageSize = data['imageSize']
            else:
                imageSize = None
            lineColor = data['lineColor']
            fillColor = data['fillColor']
            shapes = (
                (
                    s['label'],
                    s['points'],
                    s['line_color'],
                    s['fill_color'],
                    s.get('shape_type', 'polygon'),
                )
                for s in data['shapes']
            )
        except Exception as e:
            raise LabelFileError(e)

        otherData = {}
        for key, value in data.items():
            if key not in keys:
                otherData[key] = value

        # Only replace data after everything is loaded.
        self.flags = flags
        self.shapes = shapes
        self.imagePath = imagePath
        self.imageData = imageData
        self.imageSize = imageSize
        self.lineColor = lineColor
        self.fillColor = fillColor
        self.filename = filename
        self.otherData = otherData

    def save(self, filename, shapes, imagePath, imageSize, imageData=None,
             lineColor=None, fillColor=None, otherData=None,
             flags=None):
        if imageData is not None:
            imageData = base64.b64encode(imageData).decode('utf-8')
        if otherData is None:
            otherData = {}
        if flags is None:
            flags = []
        data = dict(
            version=__version__,
            flags=flags,
            shapes=shapes,
            lineColor=lineColor,
            fillColor=fillColor,
            imagePath=imagePath,
            imageData=imageData,
            imageSize=imageSize,
        )
        for key, value in otherData.items():
            data[key] = value
        try:
            with open(filename, 'wb' if PY2 else 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.filename = filename
        except Exception as e:
            raise LabelFileError(e)

    @staticmethod
    def isLabelFile(filename):
        return os.path.splitext(filename)[1].lower() == LabelFile.suffix
