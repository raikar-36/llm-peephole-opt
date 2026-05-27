define dso_local i32 @f_x001(i32 noundef %0) local_unnamed_addr #0 {
  %2 = icmp eq i32 %0, 0
  br i1 %2, label %7, label %3

3:                                                ; preds = %1
  %4 = tail call i32 @llvm.ctpop.i32(i32 %0), !range !5
  %5 = icmp ult i32 %4, 2
  %6 = zext i1 %5 to i32
  br label %7

7:                                                ; preds = %3, %1
  %8 = phi i32 [ 0, %1 ], [ %6, %3 ]
  ret i32 %8
}
