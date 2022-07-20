function out    = spmSegment(structural_fn, spm_dir, dcm2nii_dir)
    %Based on https://github.com/jsheunis/matlab-spm-scripts-jsh
    %Calls SPM_jobman to segment the wm & gm of the supplied structural image.

    %Inputs:
    %structural_fn  - character array of the filename of the structural image.
    %spm_dir        - character array of the location of the spm directory.

    %Returns:
    %out    - struct with the following fields:
    %   - wm:       filename of the wm segmentation mask
    %   - gm:       filename of the gm segmentation mask
    %   - remove:   list of all the other files that are produced that can
    %               %safely be removed.                
    
    addpath(genpath(spm_dir))
    addpath(genpath(dcm2nii_dir))
    
    %First, create a .nii image from the dicom
    %Find dcm2niix path.
    dcm2nii = strcat(dcm2nii_dir, '\dcm2niix');
    
    %Create a new directory for the .nii and the segmentation
    [direc, ~, ~]    = fileparts(structural_fn);
    newDir              = strcat(direc, filesep, 'StructuralNii');
    if ~exist(newDir, 'dir')
        mkdir(newDir);
    end
    newSegDir       = strcat(direc, filesep, 'Segmentation');
    if ~exist(newSegDir, 'dir')
        mkdir(newSegDir);
    end
    
    
    %Check if previously made nii files exist, don't make any new ones if
    %that's the case.
    if numel(dir(newDir)) <= 2
    
        %Call the dcm2nii command
    %     cmd = [dcm2nii ' -f "' fn '" -o "' newDir '"'];
        cmd = [dcm2nii ' -f %p_%s -o "' newDir '" "'  structural_fn '"'];
        system(cmd);


        %Remove any unnecessary files
        phNii   = dir(fullfile(newDir, '*_ph.nii'));
        if ~isempty(phNii)
            delete(fullfile(phNii.folder, phNii.name));
        end

        phNii   = dir(fullfile(newDir, '*_pha.nii'));
        if ~isempty(phNii)
            delete(fullfile(phNii.folder, phNii.name));
        end
        
        phJson  = dir(fullfile(newDir, '*_ph.json'));
        if ~isempty(phJson)
            delete(fullfile(phJson.folder, phJson.name));
        end

        phJson  = dir(fullfile(newDir, '*_pha.json'));
        if ~isempty(phJson)
            delete(fullfile(phJson.folder, phJson.name));
        end

        aNii   = dir(fullfile(newDir, '*_a.nii'));
        if ~isempty(aNii)
            delete(fullfile(aNii.folder, aNii.name));
        end

        aJson   = dir(fullfile(newDir, '*_a.json'));
        if ~isempty(aJson)
            delete(fullfile(aJson.folder, aJson.name));
        end
    end
    
    %Find the right .nii file:
    item   = dir(fullfile(newDir, '*.nii'));
    segment_fn      = fullfile(item.folder, item.name);    
    
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %Next, perform the segmentation
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    %If the files already exist, return those
    [~, f, e] = fileparts(segment_fn);
    if exist([newSegDir filesep 'c2' f e], 'file') ~= 0
        out = [newSegDir filesep 'c2' f e];
        return
    end
    
    %Initiate
    spm('defaults','fmri');
    spm_jobman('initcfg');
    segmentation = struct;

    %Prepare parameters for segmentation
    % Channel
    segmentation.mb{1}.spm.spatial.preproc.channel.biasreg = 0.001;
    segmentation.mb{1}.spm.spatial.preproc.channel.biasfwhm = 60;
    segmentation.mb{1}.spm.spatial.preproc.channel.write = [0 1];
    segmentation.mb{1}.spm.spatial.preproc.channel.vols = {segment_fn};
    % Tissue

    for t = 1:6
        segmentation.mb{1}.spm.spatial.preproc.tissue(t).tpm = {[spm_dir filesep 'tpm' filesep 'TPM.nii,' num2str(t)]};
        segmentation.mb{1}.spm.spatial.preproc.tissue(t).ngaus = t-1;
        segmentation.mb{1}.spm.spatial.preproc.tissue(t).native = [1 0];
        segmentation.mb{1}.spm.spatial.preproc.tissue(t).warped = [0 0];
    end
    % Warp
    segmentation.mb{1}.spm.spatial.preproc.warp.mrf = 1;
    segmentation.mb{1}.spm.spatial.preproc.warp.cleanup = 1;
    segmentation.mb{1}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
    segmentation.mb{1}.spm.spatial.preproc.warp.affreg = 'mni';
    segmentation.mb{1}.spm.spatial.preproc.warp.fwhm = 0;
    segmentation.mb{1}.spm.spatial.preproc.warp.samp = 3;
    segmentation.mb{1}.spm.spatial.preproc.warp.write=[1 1];

    %
    % Run
    spm_jobman('run',segmentation.mb);
    
    [d, f, e] = fileparts(segment_fn);    
    %Remove all unnecessary files
    delete([d filesep 'y_' f e]);
    delete([d filesep 'iy_' f e]);
    delete([d filesep 'm' f e]);
    delete([d filesep 'c1' f e]);
    delete([d filesep 'c3' f e]);
    delete([d filesep 'c4' f e]);
    delete([d filesep 'c5' f e]);
    delete([d filesep 'c6' f e]);
    delete([d filesep f '_seg8.mat']);

    % return filenames of all the created files
    
    movefile([d filesep 'c2' f e], [newSegDir filesep 'c2' f e]);
    out = [newSegDir filesep 'c2' f e];     %wm file

end

%%\