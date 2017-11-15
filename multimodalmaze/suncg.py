# Copyright (c) 2017, IGLU consortium
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
#  - Redistributions of source code must retain the above copyright notice, 
#    this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright notice, 
#    this list of conditions and the following disclaimer in the documentation 
#    and/or other materials provided with the distribution.
#  - Neither the name of the copyright holder nor the names of its contributors 
#    may be used to endorse or promote products derived from this software 
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT 
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, 
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.

import csv
import logging
import numpy as np

from multimodalmaze.constants import MODEL_CATEGORY_MAPPING

logger = logging.getLogger(__name__)
      
def ignoreVariant(modelId):
    suffix = "_0"
    if modelId.endswith(suffix):
        modelId =  modelId[:len(modelId) - len(suffix)]
    return modelId
      
class ModelInformation(object):

    header = 'id,front,nmaterials,minPoint,maxPoint,aligned.dims,index,variantIds'

    def __init__(self, filename):
        self.model_info = {}
        
        self._parseFromCSV(filename)
        
    def _parseFromCSV(self, filename):
        with open(filename, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            for i,row in enumerate(reader):
                if i == 0:
                    rowStr = ','.join(row)
                    assert rowStr == ModelInformation.header
                else:
                    model_id, front, nmaterials, minPoint, maxPoint, aligned_dims, _, variantIds = row
                    if model_id in self.model_info:
                        raise Exception('Model %s already exists!' % (model_id))
                    
                    front = np.fromstring(front, dtype=np.float64, sep=',')
                    nmaterials = int(nmaterials)
                    minPoint = np.fromstring(minPoint, dtype=np.float64, sep=',')
                    maxPoint = np.fromstring(maxPoint, dtype=np.float64, sep=',')
                    aligned_dims = np.fromstring(aligned_dims, dtype=np.float64, sep=',')
                    variantIds = variantIds.split(',')
                    self.model_info[model_id] = {'front':front,
                                                 'nmaterials':nmaterials,
                                                 'minPoint':minPoint,
                                                 'maxPoint':maxPoint,
                                                 'aligned_dims':aligned_dims,
                                                 'variantIds':variantIds}

    def getModelInfo(self, modelId):
        return self.model_info[ignoreVariant(modelId)]

class ModelCategoryMapping(object):

    def __init__(self, filename):
        self.model_id = []
        self.fine_grained_class = {}
        self.coarse_grained_class = {}
        self.nyuv2_40class = {}
        self.wnsynsetid = {}
        self.wnsynsetkey = {}
        
        self._parseFromCSV(filename)
        
    def _parseFromCSV(self, filename):
        with open(filename, 'rb') as f:
            reader = csv.reader(f, delimiter=',')
            for i,row in enumerate(reader):
                if i == 0:
                    rowStr = ','.join(row)
                    assert rowStr == MODEL_CATEGORY_MAPPING["header"]
                else:
                    _, model_id, fine_grained_class, coarse_grained_class, _, nyuv2_40class, wnsynsetid, wnsynsetkey = row
                    if model_id in self.model_id:
                        raise Exception('Model %s already exists!' % (model_id))
                    self.model_id.append(model_id)
                    
                    self.fine_grained_class[model_id] = fine_grained_class
                    self.coarse_grained_class[model_id] = coarse_grained_class
                    self.nyuv2_40class[model_id] = nyuv2_40class
                    self.wnsynsetid[model_id] = wnsynsetid
                    self.wnsynsetkey[model_id] = wnsynsetkey

    def _printFineGrainedClassListAsDict(self):
        for c in sorted(set(self.fine_grained_class.values())):
            name = c.replace("_", " ")
            print "'%s':'%s'," % (c, name)
    
    def _printCoarseGrainedClassListAsDict(self):
        for c in sorted(set(self.coarse_grained_class.values())):
            name = c.replace("_", " ")
            print "'%s':'%s'," % (c, name)
    
    def getFineGrainedCategoryForModelId(self, modelId):
        return self.fine_grained_class[ignoreVariant(modelId)]
    
    def getCoarseGrainedCategoryForModelId(self, modelId):
        return self.coarse_grained_class[ignoreVariant(modelId)]
    
    def getFineGrainedClassList(self):
        return sorted(set(self.fine_grained_class.values()))
    
    def getCoarseGrainedClassList(self):
        return sorted(set(self.coarse_grained_class.values()))
    

class ObjectVoxelData(object):
    
    def __init__(self, voxels, translation, scale):
        self.voxels = voxels
        self.translation = translation
        self.scale = scale
    
    def getFilledVolume(self):
        nbFilledVoxels = np.count_nonzero(self.voxels)
        perVoxelVolume = self.scale / np.prod(self.voxels.shape)
        return nbFilledVoxels * perVoxelVolume
    
    @staticmethod
    def fromFile(filename):
        
        with open(filename, 'rb') as f:
            
            # Read header line and version
            line = f.readline().decode('ascii').strip() # u'#binvox 1'
            header, version = line.split(" ")
            if header != '#binvox':
                raise Exception('Unable to read header from file: %s' % (filename))
            version = int(version)
            assert version == 1
            
            # Read dimensions and transforms
            line = f.readline().decode('ascii').strip() # u'dim 128 128 128'
            items = line.split(" ")
            assert items[0] == 'dim'
            depth, height, width = np.fromstring(" ".join(items[1:]), sep=' ', dtype=np.int)
            
            # XXX: what is this translation component?
            line = f.readline().decode('ascii').strip() # u'translate -0.176343 -0.356254 0.000702'
            items = line.split(" ")
            assert items[0] == 'translate'
            translation = np.fromstring(" ".join(items[1:]), sep=' ', dtype=np.float)
            
            line = f.readline().decode('ascii').strip() # u'scale 0.863783'
            items = line.split(" ")
            assert items[0] == 'scale'
            scale = float(items[1])
            
            # Read voxel data
            line = f.readline().decode('ascii').strip() # u'data'
            assert line == 'data'
            
            size = width * height * depth
            voxels = np.zeros((size,), dtype=np.int8)
            
            nrVoxels = 0
            index = 0
            endIndex = 0
            while endIndex < size:
                value = np.fromstring(f.read(1), dtype=np.uint8)[0]
                count = np.fromstring(f.read(1), dtype=np.uint8)[0]
                endIndex = index + count
                assert endIndex <= size
                
                voxels[index:endIndex] = value
                if value != 0:
                    nrVoxels += count
                index = endIndex
            
            # NOTE: we should by now have reach the end of the file
            assert f.readline() == ''
            
            # FIXME: not sure about the particular dimension ordering here!
            voxels = voxels.reshape((width, height, depth))
            
            logger.debug('Number of non-empty voxels read from file: %d' % (nrVoxels))
        
        return ObjectVoxelData(voxels, translation, scale)
    