define i32 @chain_or_or_255_255(i32 %x) {
entry:
  %tmp = or i32 %x, 255
  %result = or i32 %tmp, 255
  ret i32 %result
}
