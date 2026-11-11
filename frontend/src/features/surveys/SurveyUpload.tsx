import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Upload, Camera, FileImage, CheckCircle } from 'lucide-react';

interface SurveyUploadProps {
  onUploadSuccess?: () => void;
}

export const SurveyUpload: React.FC<SurveyUploadProps> = ({ onUploadSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const valid = Array.from(files).filter(f => f.type.startsWith('image/'));
    setSelectedFiles(prev => [...prev, ...valid]);
  };

  const handleSimulatedUpload = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    // Simulate upload progress
    await new Promise(r => setTimeout(r, 1200));
    setUploading(false);
    setUploadSuccess(true);
    setSelectedFiles([]);
    if (onUploadSuccess) onUploadSuccess();
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Upload Demolition Site Imagery</CardTitle>
        <CardDescription>
          Supports handheld high-res surveyor photos, drone orthomosaics, and 360° spherical site scans.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
            dragActive
              ? 'border-emerald-500 bg-emerald-500/10'
              : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
          }`}
        >
          <Camera className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p className="text-sm font-semibold text-slate-200">
            Drag & drop site inspection photos here, or click to browse
          </p>
          <p className="text-xs text-slate-500 mt-1">
            JPEG, PNG, TIFF up to 50MB per orthophoto tile. EXIF GPS coordinates will be preserved.
          </p>
          <input
            type="file"
            multiple
            accept="image/*"
            className="hidden"
            id="file-upload"
            onChange={(e) => handleFiles(e.target.files)}
          />
          <label htmlFor="file-upload" className="inline-block mt-4">
            <span className="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer border border-slate-700">
              Select Photos
            </span>
          </label>
        </div>

        {selectedFiles.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-slate-300">
              Ready to upload ({selectedFiles.length} files selected):
            </div>
            <div className="max-h-36 overflow-y-auto space-y-1">
              {selectedFiles.map((file, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded bg-slate-800/60 text-xs">
                  <div className="flex items-center gap-2 truncate">
                    <FileImage className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span className="truncate">{file.name}</span>
                  </div>
                  <span className="text-slate-400">{(file.size / (1024 * 1024)).toFixed(1)} MB</span>
                </div>
              ))}
            </div>

            <Button
              className="w-full mt-3"
              isLoading={uploading}
              onClick={handleSimulatedUpload}
            >
              <Upload className="w-4 h-4" />
              Upload & Queue for AI Processing
            </Button>
          </div>
        )}

        {uploadSuccess && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300">
            <CheckCircle className="w-4 h-4 flex-shrink-0 text-emerald-400" />
            <span>Images uploaded successfully to S3 storage and registered to the active survey session.</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
