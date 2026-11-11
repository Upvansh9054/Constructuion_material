import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import {
  Camera,
  Video,
  FileImage,
  Sparkles,
  Sliders,
  CheckCircle2,
  Trash2,
} from 'lucide-react';

interface StagedFile {
  id: string;
  name: string;
  size: number;
  type: 'IMAGE' | 'VIDEO' | 'ORTHO';
  previewUrl?: string;
  status: 'QUEUED' | 'UPLOADING' | 'UPLOADED';
}

interface SiteUploadScreenProps {
  projectId?: string;
  onUploadComplete: () => void;
  onCancel: () => void;
}

export const SiteUploadScreen: React.FC<SiteUploadScreenProps> = ({
  onUploadComplete,
  onCancel,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [flightAltitudeMeters, setFlightAltitudeMeters] = useState('45');
  const [focalLengthMm, setFocalLengthMm] = useState('8.8');
  const [sensorWidthMm, setSensorWidthMm] = useState('13.2');
  const [cameraSource, setCameraSource] = useState('DRONE_ORTHOMOSAIC');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Pre-staged sample demolition inspection files for turnkey demonstration
  const [files, setFiles] = useState<StagedFile[]>([
    {
      id: 'f-1',
      name: 'DJI_20261102_001_North_Elevation_Ortho.jpg',
      size: 14.8 * 1024 * 1024,
      type: 'ORTHO',
      previewUrl: 'https://images.unsplash.com/photo-1541888946425-d0fbb186156f?q=80&w=300&auto=format&fit=crop',
      status: 'QUEUED',
    },
    {
      id: 'f-2',
      name: 'IMG_20261102_Mezzanine_Steel_Trusses.jpg',
      size: 8.2 * 1024 * 1024,
      type: 'IMAGE',
      previewUrl: 'https://images.unsplash.com/photo-1504307651254-35680f356dfd?q=80&w=300&auto=format&fit=crop',
      status: 'QUEUED',
    },
    {
      id: 'f-3',
      name: 'DSC_4421_Basement_Foundation_Footings.jpg',
      size: 11.4 * 1024 * 1024,
      type: 'IMAGE',
      previewUrl: 'https://images.unsplash.com/photo-1589939705384-5185137a7f0f?q=80&w=300&auto=format&fit=crop',
      status: 'QUEUED',
    },
    {
      id: 'f-4',
      name: 'WALKTHROUGH_Boiler_Room_Roof_360.mp4',
      size: 42.1 * 1024 * 1024,
      type: 'VIDEO',
      status: 'QUEUED',
    },
  ]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (!e.dataTransfer.files) return;

    const newFiles: StagedFile[] = Array.from(e.dataTransfer.files).map((f, i) => ({
      id: `f-drop-${Date.now()}-${i}`,
      name: f.name,
      size: f.size,
      type: f.type.includes('video') ? 'VIDEO' : 'IMAGE',
      status: 'QUEUED',
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const handleStartUpload = () => {
    setIsUploading(true);
    // Simulate batch S3 presigned URL generation and upload
    setTimeout(() => {
      setIsUploading(false);
      setUploadSuccess(true);
      setFiles((prev) => prev.map((f) => ({ ...f, status: 'UPLOADED' })));
      setTimeout(() => {
        onUploadComplete();
      }, 1000);
    }, 1500);
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Demolition Projects', onClick: onCancel },
          { label: 'Site Media Upload & Survey Calibration' },
        ]}
      />

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Site Image & Video Upload
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Stream high-resolution photogrammetric drone scans, site DSLR walk-throughs, and video recordings to S3
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onCancel}>
            Back
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleStartUpload}
            isLoading={isUploading}
            disabled={files.length === 0}
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            Upload & Launch AI Inference ({files.length})
          </Button>
        </div>
      </div>

      {/* Photogrammetric Calibration Panel */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <CardTitle className="text-sm">Photogrammetry & Camera Calibration</CardTitle>
            </div>
            <span className="text-[11px] text-slate-500 font-mono">
              GSD Formula: (Altitude × Sensor Width) / (Focal Length × Image Width)
            </span>
          </div>
          <CardDescription className="text-xs">
            Calibrate ground sample distance (GSD) for accurate volumetric ($m^3$) and tonnage estimation from 2D bounds
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <Select
              label="Capture Device"
              value={cameraSource}
              onChange={(e) => setCameraSource(e.target.value)}
            >
              <option value="DRONE_ORTHOMOSAIC">Drone Orthomosaic (UAV)</option>
              <option value="HANDHELD_INSPECTION">Handheld DSLR / Mobile</option>
              <option value="360_SCAN">360° Spherical Scanner</option>
              <option value="POINT_CLOUD">LiDAR RGB-D Scanner</option>
            </Select>

            <Input
              label="Flight Altitude (m AGL)"
              type="number"
              value={flightAltitudeMeters}
              onChange={(e) => setFlightAltitudeMeters(e.target.value)}
              helperText="Above Ground Level"
            />

            <Input
              label="Focal Length (mm)"
              type="number"
              value={focalLengthMm}
              onChange={(e) => setFocalLengthMm(e.target.value)}
              helperText="Lens optical focal length"
            />

            <Input
              label="Sensor Width (mm)"
              type="number"
              value={sensorWidthMm}
              onChange={(e) => setSensorWidthMm(e.target.value)}
              helperText="Camera sensor physical width"
            />
          </div>
        </CardContent>
      </Card>

      {/* Drag & Drop Upload Staging */}
      <Card>
        <CardContent className="p-6">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
              dragActive
                ? 'border-emerald-500 bg-emerald-500/10'
                : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-center gap-3 mb-3 text-slate-500">
              <Camera className="w-8 h-8 text-emerald-400" />
              <Video className="w-8 h-8 text-blue-400" />
            </div>
            <h3 className="text-sm font-bold text-slate-200">
              Drag & Drop Drone Flights, Site Orthomosaics, or Inspection Video
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              JPEG, PNG, TIFF, or MP4 video files up to 200MB per file. High-resolution orthophotos are automatically
              tiled using SAHI slicing for small debris segmentation.
            </p>

            <input
              type="file"
              multiple
              accept="image/*,video/*"
              className="hidden"
              id="upload-media"
              onChange={(e) => {
                if (e.target.files) {
                  const newFiles: StagedFile[] = Array.from(e.target.files).map((f, i) => ({
                    id: `f-${Date.now()}-${i}`,
                    name: f.name,
                    size: f.size,
                    type: f.type.includes('video') ? 'VIDEO' : 'IMAGE',
                    status: 'QUEUED',
                  }));
                  setFiles((prev) => [...prev, ...newFiles]);
                }
              }}
            />
            <label htmlFor="upload-media" className="inline-block mt-4">
              <span className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer border border-slate-700">
                Browse Files
              </span>
            </label>
          </div>

          {/* Staged Files List */}
          {files.length > 0 && (
            <div className="mt-6 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold text-slate-300">
                  Staged Media for S3 Streaming ({files.length} items • {(files.reduce((a, b) => a + b.size, 0) / (1024 * 1024)).toFixed(1)} MB total)
                </span>
                <button
                  onClick={() => setFiles([])}
                  className="text-rose-400 hover:underline text-[11px]"
                >
                  Clear All
                </button>
              </div>

              <div className="divide-y divide-slate-800/80 rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
                {files.map((file) => (
                  <div key={file.id} className="p-3 flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-3 truncate">
                      {file.previewUrl ? (
                        <img
                          src={file.previewUrl}
                          alt=""
                          className="w-10 h-10 rounded object-cover border border-slate-700 flex-shrink-0"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0 text-slate-400">
                          {file.type === 'VIDEO' ? <Video className="w-4 h-4" /> : <FileImage className="w-4 h-4" />}
                        </div>
                      )}

                      <div className="truncate">
                        <div className="font-semibold text-white truncate">{file.name}</div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-2">
                          <span>{(file.size / (1024 * 1024)).toFixed(1)} MB</span>
                          <span>•</span>
                          <span className="uppercase text-[10px] tracking-wider text-slate-500">{file.type}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {file.status === 'UPLOADED' ? (
                        <span className="flex items-center gap-1 text-emerald-400 text-xs font-semibold">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Uploaded
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                          {file.status}
                        </span>
                      )}
                      <button
                        onClick={() => removeFile(file.id)}
                        className="p-1 rounded text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {uploadSuccess && (
            <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
              <div>
                <span className="font-semibold block">All files uploaded successfully via S3 presigned URLs.</span>
                <span className="text-slate-400">Dispatching Celery worker task for YOLO material detection...</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
