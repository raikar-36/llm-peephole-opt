define i32 @chain_sub_add_1_1(i32 %x) {
entry:
  %tmp = sub i32 %x, 1
  %result = add i32 %tmp, 1
  ret i32 %result
}
