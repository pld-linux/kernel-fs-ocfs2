#
# Condtional build:
%bcond_without	kernel          # don't build kernel modules
%bcond_without	dist_kernel	# without distribution kernel
%bcond_without	smp		# without smp packages
%bcond_with	verbose		# verbose build (V=1)
#
%define _rel	0.1
Summary:	Oracle Cluster File System
Name:		kernel-fs-ocfs2
Version:	1.1.2
Release:	%{_rel}@%{_kernel_ver_str}
Epoch:		0
License:	GPL v2
Group:		Base/Kernel
Source0:	http://oss.oracle.com/projects/ocfs2/dist/files/source/v1.1/ocfs2-%{version}.tar.gz
# Source0-md5:	d50680c60cd5210b4581febb2f5807ff
URL:		http://sources.redhat.com/cluster/ocfs2/
%if %{with kernel}
%{?with_dist_kernel:BuildRequires:	kernel-module-build >= 2.6.7}
%endif
BuildRequires:	perl-base
%{?with_dist_kernel:%requires_releq_kernel_up}
Requires(post,postun):	/sbin/depmod
%{?with_dist_kernel:Requires(postun):	kernel}
Buildroot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
OCFS2 is the next generation of the Oracle Cluster File System for
Linux. It is an extent based, POSIX compliant file system. Unlike the
previous release (OCFS), OCFS2 is a general-purpose file system that
can be used for shared Oracle home installations making management of
Oracle Real Application Cluster (RAC) installations even easier. Among
the new features and benefits are:
- Node and architecture local files using Context Dependent Symbolic
  Links (CDSL)
- Network based pluggable DLM
- Improved journaling / node recovery using the Linux Kernel "JBD"
  subsystem
- Improved performance of meta-data operations (space allocation,
  locking, etc).
- Improved data caching / locking (for files such as oracle binaries,
  libraries, etc)

%package -n kernel-smp-fs-ocfs2
Summary:	Oracle Cluster File System
Release:	%{_rel}@%{_kernel_ver_str}
Group:		Base/Kernel
%{?with_dist_kernel:%requires_releq_kernel_smp}
Requires(post,postun):	/sbin/depmod
%{?with_dist_kernel:Requires(postun):	kernel-smp}

%description -n kernel-smp-fs-ocfs2
Oracle Cluster File System.

%prep
%setup -q -n ocfs2-%{version}

%build
%configure \
	--with-kernel=%{_kernelsrcdir} \
	--enable-debug=no

for cfg in %{?with_dist_kernel:%{?with_smp:smp} up}%{!?with_dist_kernel:nondist}; do
    if [ ! -r "%{_kernelsrcdir}/config-$cfg" ]; then
	exit 1
    fi
    rm -rf include
    install -d include/{linux,config}
    ln -sf %{_kernelsrcdir}/config-$cfg .config
    ln -sf %{_kernelsrcdir}/include/linux/autoconf-$cfg.h include/linux/autoconf.h
    ln -sf %{_kernelsrcdir}/include/asm-%{_target_base_arch} include/asm
    %if %{without dist_kernel}
        [ ! -x %{_kernelsrcdir}/scripts/kallsyms ] || ln -sf %{_kernelsrcdir}/scripts
    %endif
    touch include/config/MARKER
    %{__make} -C %{_kernelsrcdir} clean \
	RCS_FIND_IGNORE="-name '*.ko' -o" \
	M=$PWD O=$PWD \
	%{?with_verbose:V=1}
    %{__make} -C %{_kernelsrcdir} modules \
	RCS_FIND_IGNORE="-name '*.ko' -o" \
	CC="%{__cc}" CPP="%{__cpp}" \
	M=$PWD O=$PWD \
	%{?with_verbose:V=1}
	mv lock_${dir}.ko lock_${dir}-$cfg.ko
done

%install
rm -rf $RPM_BUILD_ROOT

%if %{with kernel}
# DLM
install -d $RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}{,smp}/kernel/fs/ocfs2_locking/lock_dlm
install src/dlm/lock_dlm-%{?with_dist_kernel:up}%{!?with_dist_kernel:nondist}.ko \
	$RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}/kernel/fs/ocfs2_locking/lock_dlm/lock_dlm.ko
%if %{with smp} && %{with dist_kernel}
install src/dlm/lock_dlm-smp.ko \
	$RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}smp/kernel/fs/ocfs2_locking/lock_dlm/lock_dlm.ko
%endif
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
%depmod %{_kernel_ver}

%postun
%depmod %{_kernel_ver}

%post -n kernel-smp-fs-ocfs2
%depmod %{_kernel_ver}smp

%postun -n kernel-smp-fs-ocfs2
%depmod %{_kernel_ver}smp

%if %{with kernel}
%files
%defattr(644,root,root,755)
/lib/modules/%{_kernel_ver}/kernel/fs/*

%if %{with smp} && %{with dist_kernel}
%files -n kernel-smp-fs-ocfs2
%defattr(644,root,root,755)
/lib/modules/%{_kernel_ver}smp/kernel/fs/*
%endif
%endif
