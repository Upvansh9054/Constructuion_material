import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Building,
  Cpu,
  Database,
  CheckCircle2,
  Key,
} from 'lucide-react';

interface SettingsScreenProps {
  user: { email: string; role: string; name: string };
  onUpdateUser: (userData: { email: string; role: string; name: string }) => void;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({ user, onUpdateUser }) => {
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [companyName, setCompanyName] = useState('Apex Demolition Group');
  const [licenseNumber, setLicenseNumber] = useState('IL-DEMO-2024-8891');
  const [defaultConfidence, setDefaultConfidence] = useState('0.45');
  const [defaultAltitude, setDefaultAltitude] = useState('45');
  const [epaDiversionTarget, setEpaDiversionTarget] = useState('70');
  const [s3Endpoint, setS3Endpoint] = useState('http://localhost:9000');
  const [s3Bucket, setS3Bucket] = useState('demolition-surveys');
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdateUser({ ...user, name, email });
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            User Profile & System Settings
          </h2>
          <p className="text-xs text-slate-400">
            Configure contractor enterprise credentials, AI computer vision defaults, and storage connectivity
          </p>
        </div>

        {isSaved && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-emerald-500/20 text-emerald-300 text-xs font-semibold">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Settings updated successfully
          </div>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Contractor Profile */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Building className="w-4 h-4 text-emerald-400" /> Contractor & Organization Profile
            </CardTitle>
            <CardDescription className="text-xs">
              Primary company credentials printed on certified Demolition Material Audit Reports (DMAR)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Full Name / Authorized Surveyor *"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <Input
                label="Corporate Email *"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Input
                label="Company / Enterprise Name *"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
              />
              <Input
                label="Contractor Demolition License #"
                value={licenseNumber}
                onChange={(e) => setLicenseNumber(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* AI Inference & Photogrammetry Defaults */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Cpu className="w-4 h-4 text-blue-400" /> AI Computer Vision & Calibration Defaults
            </CardTitle>
            <CardDescription className="text-xs">
              Default runtime thresholds for the YOLOv8 material segmentation model
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Input
                label="Default Confidence Threshold"
                type="number"
                step="0.05"
                min="0.1"
                max="0.95"
                value={defaultConfidence}
                onChange={(e) => setDefaultConfidence(e.target.value)}
                helperText="Minimum model prediction confidence"
              />
              <Input
                label="Default Flight Altitude (m AGL)"
                type="number"
                value={defaultAltitude}
                onChange={(e) => setDefaultAltitude(e.target.value)}
                helperText="Baseline drone mission height"
              />
              <Input
                label="EPA Diversion Target (%)"
                type="number"
                value={epaDiversionTarget}
                onChange={(e) => setEpaDiversionTarget(e.target.value)}
                helperText="C&D waste landfill diversion goal"
              />
            </div>
          </CardContent>
        </Card>

        {/* S3 Storage & Model Infrastructure */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Database className="w-4 h-4 text-teal-400" /> Infrastructure & Object Storage Integration
            </CardTitle>
            <CardDescription className="text-xs">
              S3-compatible bucket configuration for raw survey orthophotos and annotated images
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="S3 Endpoint URL"
                value={s3Endpoint}
                onChange={(e) => setS3Endpoint(e.target.value)}
                helperText="MinIO local or AWS S3 endpoint"
              />
              <Input
                label="S3 Bucket Name"
                value={s3Bucket}
                onChange={(e) => setS3Bucket(e.target.value)}
              />
            </div>

            <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Key className="w-4 h-4 text-emerald-400" />
                <div>
                  <span className="font-semibold text-white block">OpenAI Generative Synthesis Engine</span>
                  <span className="text-[11px] text-slate-400">
                    Powers executive summaries and buyer matching in DMAR audit reports
                  </span>
                </div>
              </div>
              <span className="flex items-center gap-1.5 text-emerald-400 font-bold font-mono text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected
              </span>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-3">
          <Button type="submit" variant="primary">
            Save System Settings
          </Button>
        </div>
      </form>
    </div>
  );
};
