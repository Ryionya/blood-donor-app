import cloudinary.uploader
from cloudinary_storage.storage import MediaCloudinaryStorage


class SmartCloudinaryStorage(MediaCloudinaryStorage):
    """
    Custom storage that uploads PDFs and documents to Cloudinary's
    raw endpoint instead of image endpoint.
    """
    
    RAW_EXTENSIONS = ['.pdf', '.doc', '.docx']
    
    def _get_resource_type(self, name):
        import os
        ext = os.path.splitext(name)[1].lower()
        if ext in self.RAW_EXTENSIONS:
            return 'raw'
        return 'image'
    
    def _save(self, name, content):
        # Fix Windows backslashes
        name = name.replace('\\', '/')
        
        resource_type = self._get_resource_type(name)
        
        options = {
            'resource_type': resource_type,
            'use_filename': True,
            'unique_filename': True,
            'overwrite': False,
        }
        
        # Add prefix from settings
        from django.conf import settings
        prefix = settings.CLOUDINARY_STORAGE.get('PREFIX', '')
        public_id = f"{prefix}/{name}" if prefix else name
        
        # Remove file extension from public_id for Cloudinary
        import os
        public_id = os.path.splitext(public_id)[0]
        public_id = public_id.replace('\\', '/')  # fix again after join
        
        options['public_id'] = public_id
        
        response = cloudinary.uploader.upload(content, **options)
        return response['public_id']
    
    def url(self, name):
        import cloudinary
        import os
        
        ext = os.path.splitext(name)[1].lower()
        if not ext:
            # Try to detect from the name if no extension
            if 'pdf' in name.lower():
                resource_type = 'raw'
            else:
                resource_type = 'image'
        elif ext in self.RAW_EXTENSIONS:
            resource_type = 'raw'
        else:
            resource_type = 'image'
        
        return cloudinary.CloudinaryResource(
            name,
            resource_type=resource_type
        ).build_url()