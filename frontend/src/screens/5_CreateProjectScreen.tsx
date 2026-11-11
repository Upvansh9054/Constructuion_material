import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select } from '../components/ui/select';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { DemolitionSite } from '../types/site';
import {
  Building2,
  MapPin,
  Calendar,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';

interface CreateProjectScreenProps {
  onProjectCreated: (newProject: DemolitionSite) => void;
  onCancel: () => void;
}

export const CreateProjectScreen: React.FC<CreateProjectScreenProps> = ({
  onProjectCreated,
  onCancel,
}) => {
  const [name, setName] = useState('');
  const [siteCode, setSiteCode] = useState('');
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [country, setCountry] = useState('USA');
  const [latitude, setLatitude] = useState('41.8781');
  const [longitude, setLongitude] = useState('-87.6298');
  const [status, setStatus] = useState<any>('PLANNING');
  const [estimatedDemolitionDate, setEstimatedDemolitionDate] = useState('2026-12-01');
  const [footprintM2, setFootprintM2] = useState('25000');
  const [hasHazardFlags, setHasHazardFlags] = useState(false);
  const [hazardNotes, setHazardNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !siteCode || !address || !city) return;

    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      const newSite: DemolitionSite = {
        id: `prj-${Date.now().toString().slice(-4)}`,
        name,
        site_code: siteCode.toUpperCase(),
        description,
        address,
        city,
        postal_code: postalCode,
        country,
        latitude: parseFloat(latitude) || undefined,
        longitude: parseFloat(longitude) || undefined,
        status,
        estimated_demolition_date: estimatedDemolitionDate,
        contractor_id: 'usr-contractor-01',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      onProjectCreated(newSite);
    }, 600);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Demolition Projects', onClick: onCancel },
          { label: 'Register New Demolition Site' },
        ]}
      />

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Register Demolition Site
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Establish project boundaries, coordinates for haulage logistics, and survey schedules
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Core Metadata */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Building2 className="w-4 h-4 text-emerald-400" /> Site Identification
            </CardTitle>
            <CardDescription className="text-xs">
              Primary project identifiers and site code used in digital chain-of-custody transfer notes
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="sm:col-span-2">
                <Input
                  label="Project / Facility Name *"
                  placeholder="e.g. Northpoint Industrial Grain Elevator Dismantling"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div>
                <Input
                  label="Site Code (Unique) *"
                  placeholder="e.g. NGE-2026"
                  value={siteCode}
                  onChange={(e) => setSiteCode(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Site Description & Demolition Scope
              </label>
              <textarea
                rows={3}
                className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3.5 py-2 text-sm text-slate-100 placeholder-slate-500 transition-all focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/50"
                placeholder="Describe structure type (e.g. steel frame, concrete shear walls, timber roof trusses) and target selective deconstruction milestones..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Location & Spatial Mapping */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <MapPin className="w-4 h-4 text-blue-400" /> Geographic Location & Logistics Coordinates
            </CardTitle>
            <CardDescription className="text-xs">
              Used by secondary marketplace haulage calculators to compute travel distances to nearest crushing yards
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <Input
                  label="Street Address *"
                  placeholder="e.g. 1420 Harbor Terminal Boulevard"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  required
                />
              </div>
              <Input
                label="City *"
                placeholder="e.g. Chicago"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                required
              />
              <div className="grid grid-cols-2 gap-2">
                <Input
                  label="Postal Code"
                  placeholder="60609"
                  value={postalCode}
                  onChange={(e) => setPostalCode(e.target.value)}
                />
                <Input
                  label="Country"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <Input
                label="GPS Latitude"
                type="number"
                step="any"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                helperText="Georeferenced for drone flight path planning"
              />
              <Input
                label="GPS Longitude"
                type="number"
                step="any"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                helperText="Used for regional buyer radius matching"
              />
            </div>
          </CardContent>
        </Card>

        {/* Schedule & Structural Scale */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Calendar className="w-4 h-4 text-teal-400" /> Project Milestones & Scale
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Select
                label="Lifecycle Status"
                value={status}
                onChange={(e) => setStatus(e.target.value as any)}
              >
                <option value="PLANNING">Planning & Pre-Audit</option>
                <option value="PRE_DEMOLITION_SURVEY">Pre-Demolition Survey</option>
                <option value="ACTIVE_DEMOLITION">Active Demolition</option>
                <option value="MATERIAL_SORTING">Material Sorting & Haulage</option>
              </Select>

              <Input
                label="Estimated Demolition Date"
                type="date"
                value={estimatedDemolitionDate}
                onChange={(e) => setEstimatedDemolitionDate(e.target.value)}
              />

              <Input
                label="Footprint (m²)"
                type="number"
                value={footprintM2}
                onChange={(e) => setFootprintM2(e.target.value)}
                helperText="Estimated gross structural floor area"
              />
            </div>

            {/* Environmental / Hazardous Toggle */}
            <div className="pt-3 border-t border-slate-800">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasHazardFlags}
                  onChange={(e) => setHasHazardFlags(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500 w-4 h-4"
                />
                <span className="flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  Pre-Demolition Hazardous Material Flags (Asbestos, Lead, USTs)
                </span>
              </label>

              {hasHazardFlags && (
                <div className="mt-3">
                  <textarea
                    rows={2}
                    className="w-full rounded-lg border border-amber-500/40 bg-slate-900 px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
                    placeholder="Note areas of concern (e.g. pipe lagging in basement, refractory brick kiln, mastic adhesive)..."
                    value={hazardNotes}
                    onChange={(e) => setHazardNotes(e.target.value)}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={isSubmitting}>
            Register Project & Proceed to Survey Upload
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        </div>
      </form>
    </div>
  );
};
