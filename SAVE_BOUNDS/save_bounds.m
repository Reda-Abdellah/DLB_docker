% function [lower,upper]=GetBounds(sexo,edad,estructura,varargin)

% c
asym = 0;
% if nargin > 3
%     asym = 1;
% end

lower=0;
upper=0;

load tags;
if ispc
    load model;
else
    load hombre;
    load mujer;
end

s=size(tags);

%correct typos in tags
for N=1:s(1)
    p=strfind(tags{N},"Globus Pallidus");
    if  ~isempty(p)
        tags{N} = strrep(tags{N}, "Globus Pallidus", "Globus pallidus")
    end
    p=strfind(tags{N},"Hipocampus");
    if  ~isempty(p)
        tags{N} = strrep(tags{N}, "Hipocampus", "Hippocampus")
    end
    p=strfind(tags{N},"Amigdala");
    if  ~isempty(p)
        tags{N} = strrep(tags{N}, "Amigdala", "Amygdala")
    end
end
    
% Male
clear Bounds
cptR = 1;
cptC = 1;     
for N=1:s(1)
   Bounds{cptR, cptC} = tags{N};
   cptC = cptC + 1;
   asym = 0;
   p=strfind(tags{N},"Asymmetry");
   if  ~isempty(p)
       asym = 1;
   end
    for edad=1:101
        if ispc
             [ci,p]=predint(model.hombre(N).model,edad);
            lower=ci(1);
            upper=ci(2);
        else        
            lower=hombre{N}.down(edad);
            upper=hombre{N}.up(edad);
        end
                    
        if  ~asym
            tags{N}
           lower = max(lower, 0);
            upper = max(upper, 0);
        end
        
        Bounds{cptR, cptC} = lower;
        cptC = cptC + 1;
        Bounds{cptR, cptC} = upper;
        cptC = cptC + 1;
    end
    cptR = cptR + 1; 
   cptC = 1;    
end
cell2csv('male_vb_bounds.csv', Bounds, '%.12f', ';')


% Female
clear Bounds
cptR = 1;
cptC = 1;     
for N=1:s(1)
   Bounds{cptR, cptC} = tags{N};
   cptC = cptC + 1;
   asym = 0;
   p=strfind(tags{N},"Asymmetry");
   if  ~isempty(p)
       asym = 1;
   end
   
    for edad=1:101
        if ispc
             [ci,p]=predint(model.mujer(N).model,edad);
            lower=ci(1);
            upper=ci(2);
        else        
            lower=mujer{N}.down(edad);
            upper=mujer{N}.up(edad);
        end
        
        if  ~asym
           lower = max(lower, 0);
            upper = max(upper, 0);
        end
        
        Bounds{cptR, cptC} = lower;
        cptC = cptC + 1;
        Bounds{cptR, cptC} = upper;
        cptC = cptC + 1;
    end
    cptR = cptR + 1; 
   cptC = 1;    
end
cell2csv('female_vb_bounds.csv', Bounds, '%.12f', ';')

%average
clear Bounds
cptR = 1;
cptC = 1;     
for N=1:s(1)
   Bounds{cptR, cptC} = tags{N};
   cptC = cptC + 1;
   asym = 0;
   p=strfind(tags{N},"Asymmetry");
   if  ~isempty(p)
       asym = 1;
   end
    for edad=1:101
        if ispc
             [ci,p]=predint(model.hombre(N).model,edad);
            lower=ci(1);
            upper=ci(2);
             [ci,p]=predint(model.mujer(N).model,edad);
            lower=lower+ci(1);
            upper=lower+ci(2);
        else        
            lower=hombre{N}.down(edad);
            upper=hombre{N}.up(edad);
            lower=lower+mujer{N}.down(edad);
            upper=upper+mujer{N}.up(edad);
        end
        lower=lower*0.5;
        upper=upper*0.5;
        
        if  ~asym
            tags{N}
           lower = max(lower, 0);
            upper = max(upper, 0);
        end
        
        Bounds{cptR, cptC} = lower;
        cptC = cptC + 1;
        Bounds{cptR, cptC} = upper;
        cptC = cptC + 1;
    end
    cptR = cptR + 1; 
   cptC = 1;    
end
cell2csv('average_vb_bounds.csv', Bounds, '%.12f', ';')




% 
% % selec by sex
% if(strcmp(sexo,'Male'))
%   
%     if ispc
%         [ci,p]=predint(model.hombre(N).model,edad);
%         lower=ci(1);
%         upper=ci(2);
%     else        
%         lower=hombre{N}.down(edad);
%         upper=hombre{N}.up(edad);
%     end
%     
% end
% 
% if(strcmp(sexo,'Female'))   
%     
%     if ispc
%         [ci,p]=predint(model.mujer(N).model,edad);
%         lower=ci(1);
%         upper=ci(2);
%     else        
%         lower=mujer{N}.down(edad);
%         upper=mujer{N}.up(edad);
%     end
%    
% end
% 
% if lower < 0 && asym == 0
%   lower = 0;
% end



% tags = 
% 
%     'Tissue WM cm3'
%     'Tissue GM cm3'
%     'Tissue CSF cm3'
%     'Tissue Brain cm3'
%     'Tissue IC cm3'
%     'Cerebrum Total cm3'
%     'Cerebrum T GM cm3'
%     'Cerebrum T WM cm3'
%     'Cerebrum Right cm3'
%     'Cerebrum R GM cm3'
%     'Cerebrum R WM cm3'
%     'Cerebrum Left cm3'
%     'Cerebrum L GM cm3'
%     'Cerebrum L WM cm3'
%     'Cerebrum Assymetry'
%     'Cerebelum Total cm3'
%     'Cerebelum T GM cm3'
%     'Cerebelum T WM cm3'
%     'Cerebelum Right cm3'
%     'Cerebelum R GM cm3'
%     'Cerebelum R WM cm3'
%     'Cerebelum Left cm3'
%     'Cerebelum L GM cm3'
%     'Cerebelum L WM cm3'
%     'Cerebelum Assymetry'
%     'Brainstem cm3'
%     'Lateral ventricles Total cm3'
%     'Lateral ventricles Right cm3'
%     'Lateral ventricles Left cm3'
%     'Lateral ventricles Asymmetry'
%     'Caudate Total cm3'
%     'Caudate Right cm3'
%     'Caudate Left cm3'
%     'Caudate Asymmetry'
%     'Putamen Total cm3'
%     'Putamen Right cm3'
%     'Putamen Left cm3'
%     'Putamen Asymmetry'
%     'Thalamus Total cm3'
%     'Thalamus Right cm3'
%     'Thalamus Left cm3'
%     'Thalamus Asymmetry'
%     'Globus Pallidus Total cm3'
%     'Globus Pallidus Right cm3'
%     'Globus Pallidus Left cm3'
%     'Globus Pallidus Asymmetry'
%     'Hipocampus Total cm3'
%     'Hipocampus Right cm3'
%     'Hipocampus Left cm3'
%     'Hipocampus Asymmetry'
%     'Amigdala Total cm3'
%     'Amigdala Right cm3'
%     'Amigdala Left cm3'
%     'Amigdala Asymmetry'
%     'Accumbens Total cm3'
%     'Accumbens Right cm3'
%     'Accumbens Left cm3'
%     'Accumbens Asymmetry'
% 